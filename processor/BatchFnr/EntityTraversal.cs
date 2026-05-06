using Autodesk.AutoCAD.DatabaseServices;

namespace BatchFnr;

/// <summary>
/// Walks a Database's model space and every paper-space layout, yielding the
/// text-bearing entities we care about along with the layout name they live
/// in. Inspired by the entity-handling that worked in BatchFindAndReplaceV1
/// (MText, DBText, BlockReference attributes, Dimension overrides), reduced
/// to the headless managed-API equivalents.
/// </summary>
public static class EntityTraversal
{
    public readonly record struct EntityHit(
        Entity Entity,
        string Space);

    /// <summary>
    /// Enumerate every text-bearing entity in every layout (model + all paper
    /// spaces) in the supplied database. The returned <see cref="Entity"/>
    /// objects are opened ForRead — call <c>UpgradeOpen()</c> on the same
    /// transaction before mutating.
    /// </summary>
    public static IEnumerable<EntityHit> EnumerateTextBearingEntities(Database db, Transaction tr)
    {
        var layoutDict = (DBDictionary)tr.GetObject(db.LayoutDictionaryId, OpenMode.ForRead);

        foreach (DBDictionaryEntry entry in layoutDict)
        {
            var layout = (Layout)tr.GetObject(entry.Value, OpenMode.ForRead);
            string spaceName = layout.LayoutName == "Model" ? "Model" : layout.LayoutName;

            var btr = (BlockTableRecord)tr.GetObject(layout.BlockTableRecordId, OpenMode.ForRead);
            foreach (var hit in EnumerateBlock(btr, tr, spaceName))
                yield return hit;
        }
    }

    private static IEnumerable<EntityHit> EnumerateBlock(
        BlockTableRecord btr,
        Transaction tr,
        string spaceName)
    {
        foreach (ObjectId id in btr)
        {
            Entity? entity = null;
            try
            {
                entity = tr.GetObject(id, OpenMode.ForRead) as Entity;
            }
            catch
            {
                // A single broken object should not abort the layout walk.
                continue;
            }
            if (entity is null)
                continue;

            switch (entity)
            {
                case MText:
                case DBText:
                case Dimension:
                    yield return new EntityHit(entity, spaceName);
                    break;

                case BlockReference br:
                    // The BlockReference itself isn't directly text-bearing,
                    // but its visible attribute references are.
                    foreach (ObjectId attId in br.AttributeCollection)
                    {
                        AttributeReference? att = null;
                        try
                        {
                            att = tr.GetObject(attId, OpenMode.ForRead) as AttributeReference;
                        }
                        catch
                        {
                            continue;
                        }
                        if (att is not null)
                            yield return new EntityHit(att, spaceName);
                    }
                    break;
            }
        }
    }

    /// <summary>
    /// Returns the user-visible text on an entity, or <c>null</c> if the entity
    /// has no inspectable text (e.g. a Dimension with no override).
    /// For MText this is the formatting-stripped text suitable for matching.
    /// </summary>
    public static string? ReadVisibleText(Entity entity) => entity switch
    {
        MText mt => MTextStripper.Strip(mt.Contents ?? string.Empty),
        DBText t => t.TextString ?? string.Empty,
        AttributeReference a => a.TextString ?? string.Empty,
        Dimension d => HasOverrideText(d) ? d.DimensionText : null,
        _ => null,
    };

    /// <summary>
    /// Friendly type label for output (matches the names used in the spec).
    /// </summary>
    public static string TypeLabel(Entity entity) => entity switch
    {
        MText => "MText",
        DBText => "DBText",
        AttributeReference => "AttributeReference",
        Dimension => "Dimension",
        _ => entity.GetType().Name,
    };

    private static bool HasOverrideText(Dimension d)
    {
        // DimensionText is "" when the dimension shows the measured value, and
        // "." when the user explicitly suppressed the text. Anything else is an
        // author-supplied override that we can search and rewrite.
        var t = d.DimensionText;
        return !string.IsNullOrEmpty(t) && t != ".";
    }
}
