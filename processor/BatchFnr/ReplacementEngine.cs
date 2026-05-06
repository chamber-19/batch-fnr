using System.Text.RegularExpressions;

namespace BatchFnr;

/// <summary>
/// Pure (no-AutoCAD) helpers for applying find/replace pairs to a string.
///
/// Centralised here so that preview, execute, MText raw-Contents writing, and
/// MText stripped-text matching all use exactly the same semantics.
/// </summary>
public static class ReplacementEngine
{
    /// <summary>
    /// Apply every pair to <paramref name="input"/> in order. Empty find strings
    /// are skipped. Returns the resulting string (which may equal the input).
    /// </summary>
    public static string Apply(string input, IReadOnlyList<FnrPair> pairs)
    {
        if (string.IsNullOrEmpty(input) || pairs.Count == 0)
            return input;

        string current = input;
        foreach (var pair in pairs)
        {
            if (string.IsNullOrEmpty(pair.Find))
                continue;
            current = ApplyOne(current, pair);
        }
        return current;
    }

    private static string ApplyOne(string input, FnrPair pair)
    {
        if (pair.UseRegex)
        {
            var options = RegexOptions.CultureInvariant;
            if (!pair.CaseSensitive)
                options |= RegexOptions.IgnoreCase;
            try
            {
                return Regex.Replace(input, pair.Find, pair.Replace, options);
            }
            catch (ArgumentException)
            {
                // Bad regex — treat as a no-op rather than crash the batch.
                return input;
            }
        }

        if (pair.CaseSensitive)
        {
            return input.Replace(pair.Find, pair.Replace, StringComparison.Ordinal);
        }

        return input.Replace(pair.Find, pair.Replace, StringComparison.OrdinalIgnoreCase);
    }
}
