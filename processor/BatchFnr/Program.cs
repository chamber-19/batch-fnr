using System.Reflection;
using System.Runtime.InteropServices;
using System.Text.Json;

namespace BatchFnr;

/// <summary>
/// Sidecar entry point. The Tauri shell spawns this executable and talks to
/// it over newline-delimited JSON on stdin/stdout. One JSON object per line,
/// flushed after every write, exactly matching every other Chamber 19
/// sidecar. stderr is reserved for fatal/internal diagnostics only.
/// </summary>
public static class Program
{
    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.Never,
        WriteIndented = false,
    };

    public static int Main(string[] _)
    {
        string? acadDir = AutoCadAssemblyResolver.Install();
        if (acadDir is null)
        {
            Console.Error.WriteLine("ERROR: No supported AutoCAD installation found.");
            Console.Error.WriteLine("BatchFnr requires AutoCAD 2025, 2026, or 2027.");
            Console.Error.WriteLine(@"Searched: C:\Program Files\Autodesk\AutoCAD <year>\");
            return 2;
        }
        Console.Error.WriteLine($"BatchFnr resolved AutoCAD install: {acadDir}");

        // Force UTF-8 on stdin/stdout so unicode in DWG text round-trips
        // unchanged regardless of the parent's console code page.
        Console.InputEncoding = new System.Text.UTF8Encoding(false);
        Console.OutputEncoding = new System.Text.UTF8Encoding(false);

        // Unbuffered writer so the Tauri side sees every line immediately.
        var stdout = new StreamWriter(Console.OpenStandardOutput(), new System.Text.UTF8Encoding(false))
        {
            AutoFlush = true,
        };

        string? line;
        while ((line = Console.In.ReadLine()) is not null)
        {
            line = line.Trim();
            if (line.Length == 0)
                continue;

            try
            {
                var req = JsonSerializer.Deserialize<Request>(line, JsonOpts);
                if (req is null)
                {
                    WriteLine(stdout, new ErrorResponse { Error = "empty request" });
                    continue;
                }

                switch (req.Action)
                {
                    case "preview":
                        HandlePreview(stdout, req);
                        break;
                    case "execute":
                        HandleExecute(stdout, req);
                        break;
                    case "shutdown":
                    case "exit":
                        return 0;
                    default:
                        WriteLine(stdout, new ErrorResponse { Error = $"unknown action: {req.Action}" });
                        break;
                }
            }
            catch (JsonException jex)
            {
                WriteLine(stdout, new ErrorResponse { Error = $"invalid json: {jex.Message}" });
            }
            catch (Exception ex)
            {
                // Never let an unexpected exception take the sidecar down —
                // the Tauri shell relies on the loop to keep running.
                WriteLine(stdout, new ErrorResponse { Error = ex.Message });
            }
        }

        return 0;
    }

    private static void HandlePreview(StreamWriter stdout, Request req)
    {
        var resp = new PreviewResponse();
        foreach (string file in req.Files)
        {
            try
            {
                var hits = DrawingProcessor.Preview(file, req.Pairs);
                resp.Matches.AddRange(hits);
                resp.FilesScanned++;
            }
            catch (Exception ex)
            {
                resp.Errors.Add(new FileError { File = file, Error = ex.Message });
            }
        }
        resp.TotalMatches = resp.Matches.Count;
        WriteLine(stdout, resp);
    }

    private static void HandleExecute(StreamWriter stdout, Request req)
    {
        var resp = new ExecuteResponse();
        int processed = 0;
        int total = req.Files.Count;

        foreach (string file in req.Files)
        {
            int changes = 0;
            try
            {
                changes = DrawingProcessor.Execute(file, req.Pairs);
                if (changes > 0)
                {
                    resp.FilesModified++;
                    resp.TotalChanges += changes;
                }
            }
            catch (Exception ex)
            {
                resp.Errors.Add(new FileError { File = file, Error = ex.Message });
            }

            processed++;
            // Per-file progress event so the UI can update its progress bar.
            WriteLine(stdout, new ProgressEvent
            {
                File = file,
                Processed = processed,
                Total = total,
                Changes = changes,
            });
        }

        WriteLine(stdout, resp);
    }

    private static void WriteLine<T>(StreamWriter stdout, T payload)
    {
        // One JSON object per line, then a newline, then flush. Order matters
        // — the consumer reads line-by-line and must never see a partial line.
        stdout.WriteLine(JsonSerializer.Serialize(payload, JsonOpts));
        stdout.Flush();
    }
}

internal static class AutoCadAssemblyResolver
{
    private static readonly string[] SupportedVersions = ["2027", "2026", "2025"];
    private static readonly HashSet<string> ManagedAssemblies = new(StringComparer.OrdinalIgnoreCase)
    {
        "acdbmgd",
        "accoremgd",
        "acmgd",
        "accui",
    };

    private static string? _resolvedAcadDir;

    public static string? Install()
    {
        _resolvedAcadDir = SupportedVersions
            .Select(version => $@"C:\Program Files\Autodesk\AutoCAD {version}")
            .FirstOrDefault(Directory.Exists);

        if (_resolvedAcadDir is null)
            return null;

        if (!SetDllDirectory(_resolvedAcadDir))
        {
            Console.Error.WriteLine($"WARN: SetDllDirectory failed for '{_resolvedAcadDir}' (Win32={Marshal.GetLastWin32Error()}).");
        }
        AppDomain.CurrentDomain.AssemblyResolve += ResolveManagedAssembly;
        return _resolvedAcadDir;
    }

    private static Assembly? ResolveManagedAssembly(object? _, ResolveEventArgs args)
    {
        if (_resolvedAcadDir is null)
            return null;

        var assemblyName = new AssemblyName(args.Name).Name;
        if (assemblyName is null || !ManagedAssemblies.Contains(assemblyName))
            return null;

        var path = Path.Combine(_resolvedAcadDir, $"{assemblyName}.dll");
        return File.Exists(path) ? Assembly.LoadFrom(path) : null;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetDllDirectory(string lpPathName);
}
