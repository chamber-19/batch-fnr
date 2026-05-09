using Autodesk.AutoCAD.DatabaseServices;

namespace BatchFnr;

/// <summary>
/// Headless DWG processor: opens a file with a side <see cref="Database"/>,
/// walks every layout, and either reports matches (preview) or writes them
/// in place (execute).
///
/// All AutoCAD-touching code lives behind these two methods so that the rest
/// of the application — the stdin/stdout JSON loop, the replacement engine,
/// the MText stripper — remains testable without AutoCAD installed.
/// </summary>
public static class DrawingProcessor
{
    /// <summary>
    /// Open <paramref name="path"/> read-only and collect every match the
    /// supplied pairs would make. Does not modify the file.
    /// </summary>
    public static List<Match> Preview(string path, IReadOnlyList<FnrPair> pairs)
    {
        var matches = new List<Match>();

        try
        {
            using var db = new Database(false, true);
            
            // Test: does it crash just creating the Database, or during ReadDwgFile?
            if (!File.Exists(path))
                throw new FileNotFoundException($"File not found: {path}");
                
            db.ReadDwgFile(path, FileOpenMode.OpenForReadAndAllShare, allowCPConversion: false, password: null);
            db.CloseInput(true);

            using var tr = db.TransactionManager.StartTransaction();

            foreach (var hit in EntityTraversal.EnumerateTextBearingEntities(db, tr))
            {
                string? current = EntityTraversal.ReadVisibleText(hit.Entity);
                if (current is null)
                    continue;

                string proposed = ReplacementEngine.Apply(current, pairs);
                if (proposed == current)
                    continue;

                matches.Add(new Match
                {
                    File = path,
                    EntityType = EntityTraversal.TypeLabel(hit.Entity),
                    Layer = hit.Entity.Layer ?? string.Empty,
                    CurrentValue = current,
                    ProposedValue = proposed,
                    Space = hit.Space,
                });
            }

            tr.Commit();
        }
        catch (System.Exception ex)
        {
            throw new System.InvalidOperationException($"Failed to process {Path.GetFileName(path)}: {ex.Message}", ex);
        }

        return matches;
    }

    /// <summary>
    /// Open <paramref name="path"/> for writing, apply every pair to every
    /// matching entity, save in place. Returns the number of entity writes.
    /// Throws on file-level errors (locked, corrupt, permission denied) so
    /// the caller can record the failure and move on.
    /// </summary>
    public static int Execute(string path, IReadOnlyList<FnrPair> pairs)
    {
        int changes = 0;

        using var db = new Database(false, true);
        db.ReadDwgFile(path, FileOpenMode.OpenForReadAndWriteNoShare, allowCPConversion: false, password: null);
        db.CloseInput(true);

        using (var tr = db.TransactionManager.StartTransaction())
        {
            foreach (var hit in EntityTraversal.EnumerateTextBearingEntities(db, tr))
            {
                if (TryApply(hit.Entity, pairs))
                    changes++;
            }
            tr.Commit();
        }

        if (changes > 0)
        {
            db.SaveAs(path, DwgVersion.Current);
        }

        return changes;
    }

    private static bool TryApply(Entity entity, IReadOnlyList<FnrPair> pairs)
    {
        switch (entity)
        {
            case MText mt:
                return TryApplyMText(mt, pairs);

            case AttributeReference a:
            {
                string current = a.TextString ?? string.Empty;
                string proposed = ReplacementEngine.Apply(current, pairs);
                if (proposed == current)
                    return false;
                a.UpgradeOpen();
                a.TextString = proposed;
                return true;
            }

            case DBText t:
            {
                string current = t.TextString ?? string.Empty;
                string proposed = ReplacementEngine.Apply(current, pairs);
                if (proposed == current)
                    return false;
                t.UpgradeOpen();
                t.TextString = proposed;
                return true;
            }

            case Dimension d:
            {
                string current = d.DimensionText ?? string.Empty;
                if (string.IsNullOrEmpty(current) || current == ".")
                    return false;
                string proposed = ReplacementEngine.Apply(current, pairs);
                if (proposed == current)
                    return false;
                d.UpgradeOpen();
                d.DimensionText = proposed;
                return true;
            }
        }
        return false;
    }

    /// <summary>
    /// MText is special: <c>Contents</c> contains formatting codes such as
    /// <c>{\H2.5;OLD TEXT}</c>. We match against the stripped text so the
    /// user-supplied find string sees clean text, but we attempt to write
    /// directly back into the raw <c>Contents</c> so that surrounding
    /// formatting is preserved. If the substring isn't present in the raw
    /// form (e.g. broken across formatting codes) we fall back to writing
    /// the stripped, replaced text — losing some formatting but still
    /// honouring the user's intent.
    /// </summary>
    private static bool TryApplyMText(MText mt, IReadOnlyList<FnrPair> pairs)
    {
        string raw = mt.Contents ?? string.Empty;
        string stripped = MTextStripper.Strip(raw);
        string newStripped = ReplacementEngine.Apply(stripped, pairs);
        if (newStripped == stripped)
            return false;

        string newRaw = ReplacementEngine.Apply(raw, pairs);

        mt.UpgradeOpen();
        // Prefer the formatting-preserving rewrite when it actually changed
        // something; otherwise rewrite from the stripped version.
        mt.Contents = newRaw != raw ? newRaw : newStripped;
        return true;
    }
}
