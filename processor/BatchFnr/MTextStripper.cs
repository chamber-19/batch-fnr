using System.Text;

namespace BatchFnr;

/// <summary>
/// Minimal MTEXT formatting-code stripper.
///
/// MTEXT (AcDbMText.Contents) embeds inline formatting using backslash codes
/// and grouping braces. Examples:
///
///   {\H2.5;OLD TEXT}       — height override around "OLD TEXT"
///   {\W0.8;wide text}      — width factor
///   {\fArial|b0|i0;hello}  — font + style
///   line one\Pline two     — \P paragraph break
///   \~                     — non-breaking space
///   \\  \{  \}             — literal backslash / brace
///   \C1;red                — color
///   \L underlined \l       — underline on/off
///   \O over \o             — overline on/off
///   \Q15;                  — oblique angle
///   \pxqc;                 — paragraph properties
///   \A1;                   — alignment
///   \Sa^b;  or  \Sa/b;     — stacked fraction (we keep both halves as text)
///
/// We deliberately do NOT use System.Text.RegularExpressions here. The grammar
/// is irregular enough (especially \S stacked-text) that an explicit scanner
/// is both clearer and faster than chained regex passes.
/// </summary>
public static class MTextStripper
{
    /// <summary>
    /// Returns the visible text of an MTEXT contents string with all
    /// formatting codes and grouping braces removed.
    /// </summary>
    public static string Strip(string contents)
    {
        if (string.IsNullOrEmpty(contents))
            return contents ?? string.Empty;

        var sb = new StringBuilder(contents.Length);
        int i = 0;
        int n = contents.Length;

        while (i < n)
        {
            char c = contents[i];

            // Group braces are structural only — drop them. Escaped braces
            // (\{ \}) are handled below.
            if (c == '{' || c == '}')
            {
                i++;
                continue;
            }

            if (c != '\\')
            {
                sb.Append(c);
                i++;
                continue;
            }

            // We are at a backslash. Look at the next char to decide.
            if (i + 1 >= n)
            {
                // Trailing lone backslash — emit it literally.
                sb.Append('\\');
                i++;
                continue;
            }

            char next = contents[i + 1];

            // Literal escapes.
            switch (next)
            {
                case '\\':
                    sb.Append('\\');
                    i += 2;
                    continue;
                case '{':
                    sb.Append('{');
                    i += 2;
                    continue;
                case '}':
                    sb.Append('}');
                    i += 2;
                    continue;
                case '~':
                    // Non-breaking space — render as a normal space for matching.
                    sb.Append(' ');
                    i += 2;
                    continue;
                case 'P':
                case 'p':
                    // \P is a hard paragraph break. Use newline so that find
                    // strings spanning lines do/don't match as the user expects.
                    if (next == 'P')
                    {
                        sb.Append('\n');
                        i += 2;
                        continue;
                    }
                    // \p... is the paragraph-properties code; it terminates at ';'.
                    i = SkipUntilSemicolon(contents, i + 2);
                    continue;
            }

            // Stacked text:  \S numerator (^ | / | #) denominator ;
            if (next == 'S')
            {
                i = AppendStacked(contents, i + 2, sb);
                continue;
            }

            // Backslash-letter formatting codes that take an argument terminated
            // by ';'. The argument carries no visible text.
            //   \H, \W, \A, \C, \c, \T, \Q, \f, \F, \K, \k, \pxxx
            if (IsFormattingLetter(next))
            {
                i = SkipUntilSemicolon(contents, i + 2);
                continue;
            }

            // Standalone toggles with no argument:  \L \l \O \o \K \k
            if (next == 'L' || next == 'l' || next == 'O' || next == 'o')
            {
                i += 2;
                continue;
            }

            // Unknown backslash sequence — drop the backslash, keep the next char.
            sb.Append(next);
            i += 2;
        }

        return sb.ToString();
    }

    private static bool IsFormattingLetter(char c)
    {
        // Letters that introduce an arg-bearing code.
        return c is 'H' or 'W' or 'A' or 'C' or 'c' or 'T' or 'Q' or 'f' or 'F';
    }

    private static int SkipUntilSemicolon(string s, int start)
    {
        int i = start;
        while (i < s.Length && s[i] != ';')
            i++;
        return i < s.Length ? i + 1 : i;
    }

    /// <summary>
    /// Handles the body of a \S stacked-text run starting just past the 'S'.
    /// Format is:  numerator (^ | / | #) denominator ;
    /// We emit "num/den" so the visible characters remain searchable.
    /// </summary>
    private static int AppendStacked(string s, int start, StringBuilder sb)
    {
        int i = start;
        var num = new StringBuilder();
        var den = new StringBuilder();
        StringBuilder cur = num;
        bool seenSep = false;

        while (i < s.Length)
        {
            char c = s[i];
            if (c == ';')
            {
                i++;
                break;
            }
            if (!seenSep && (c == '^' || c == '/' || c == '#'))
            {
                seenSep = true;
                cur = den;
                i++;
                continue;
            }
            if (c == '\\' && i + 1 < s.Length)
            {
                // honor escaped chars inside stacked text
                cur.Append(s[i + 1]);
                i += 2;
                continue;
            }
            cur.Append(c);
            i++;
        }

        sb.Append(num);
        if (seenSep)
        {
            sb.Append('/');
            sb.Append(den);
        }
        return i;
    }
}
