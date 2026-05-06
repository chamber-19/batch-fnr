using System.Text.Json.Serialization;

namespace BatchFnr;

/// <summary>
/// One find/replace pair as supplied by the UI.
/// </summary>
public sealed class FnrPair
{
    [JsonPropertyName("find")]
    public string Find { get; set; } = string.Empty;

    [JsonPropertyName("replace")]
    public string Replace { get; set; } = string.Empty;

    [JsonPropertyName("case_sensitive")]
    public bool CaseSensitive { get; set; }

    [JsonPropertyName("use_regex")]
    public bool UseRegex { get; set; }
}

/// <summary>
/// One incoming command on stdin.
/// </summary>
public sealed class Request
{
    [JsonPropertyName("action")]
    public string Action { get; set; } = string.Empty;

    [JsonPropertyName("files")]
    public List<string> Files { get; set; } = new();

    [JsonPropertyName("pairs")]
    public List<FnrPair> Pairs { get; set; } = new();
}

/// <summary>
/// One detected match returned in preview / execute results.
/// </summary>
public sealed class Match
{
    [JsonPropertyName("file")]
    public string File { get; set; } = string.Empty;

    [JsonPropertyName("entity_type")]
    public string EntityType { get; set; } = string.Empty;

    [JsonPropertyName("layer")]
    public string Layer { get; set; } = string.Empty;

    [JsonPropertyName("current_value")]
    public string CurrentValue { get; set; } = string.Empty;

    [JsonPropertyName("proposed_value")]
    public string ProposedValue { get; set; } = string.Empty;

    [JsonPropertyName("space")]
    public string Space { get; set; } = string.Empty;
}

public sealed class FileError
{
    [JsonPropertyName("file")]
    public string File { get; set; } = string.Empty;

    [JsonPropertyName("error")]
    public string Error { get; set; } = string.Empty;
}

/// <summary>
/// Progress event emitted between files during execute.
/// </summary>
public sealed class ProgressEvent
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "progress";

    [JsonPropertyName("file")]
    public string File { get; set; } = string.Empty;

    [JsonPropertyName("processed")]
    public int Processed { get; set; }

    [JsonPropertyName("total")]
    public int Total { get; set; }

    [JsonPropertyName("changes")]
    public int Changes { get; set; }
}

/// <summary>
/// Final response for a preview command.
/// </summary>
public sealed class PreviewResponse
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "complete";

    [JsonPropertyName("matches")]
    public List<Match> Matches { get; set; } = new();

    [JsonPropertyName("files_scanned")]
    public int FilesScanned { get; set; }

    [JsonPropertyName("total_matches")]
    public int TotalMatches { get; set; }

    [JsonPropertyName("errors")]
    public List<FileError> Errors { get; set; } = new();
}

/// <summary>
/// Final response for an execute command.
/// </summary>
public sealed class ExecuteResponse
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "complete";

    [JsonPropertyName("total_changes")]
    public int TotalChanges { get; set; }

    [JsonPropertyName("files_modified")]
    public int FilesModified { get; set; }

    [JsonPropertyName("errors")]
    public List<FileError> Errors { get; set; } = new();
}

public sealed class ErrorResponse
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "error";

    [JsonPropertyName("error")]
    public string Error { get; set; } = string.Empty;
}
