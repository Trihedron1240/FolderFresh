from .backbone import (
    Rule,
    RuleExecutor,
    Condition,
    Action,
    NameContainsCondition,
    NameStartsWithCondition,
    NameEndsWithCondition,
    NameEqualsCondition,
    RegexMatchCondition,
    ParentFolderContainsCondition,
    FileInFolderCondition,
    ExtensionIsCondition,
    FileSizeGreaterThanCondition,
    FileAgeGreaterThanCondition,
    LastModifiedBeforeCondition,
    IsHiddenCondition,
    IsReadOnlyCondition,
    IsDirectoryCondition,
    RenameAction,
    MoveAction,
    CopyAction,
    DeleteFileAction,
    # Helper functions
    normalize_path,
    ensure_directory_exists,
    avoid_overwrite,
    is_file_accessible,
)

# Tier-1 Actions
from .tier1_actions import (
    TokenRenameAction,
    RunCommandAction,
    ArchiveAction,
    ExtractAction,
    CreateFolderAction,
    expand_tokens,
)

# Tier-1 Conditions
from .tier1_conditions import (
    ContentContainsCondition,
    DatePatternCondition,
)

# Tier-2 Metadata
from .tier2_metadata import (
    METADATA_DB,
    calculate_quick_hash,
    calculate_full_hash,
    extract_file_metadata,
)

# Tier-2 Actions
from .tier2_actions import (
    ColorLabelAction,
    AddTagAction,
    RemoveTagAction,
    DeleteToTrashAction,
    MarkAsDuplicateAction,
)

# Tier-2 Conditions
from .tier2_conditions import (
    ColorIsCondition,
    HasTagCondition,
    MetadataContainsCondition,
    MetadataFieldEqualsCondition,
    IsDuplicateCondition,
)
