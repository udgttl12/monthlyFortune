param(
  [string]$Message = "",
  [string]$Remote = "origin",
  [string]$PushBranch = "",
  [switch]$NoPush,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
  param([string[]]$Arguments)

  & git @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
  }
}

function Read-Git {
  param([string[]]$Arguments)

  $output = & git @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
  }
  return $output
}

function Test-AnyPath {
  param(
    [string[]]$Paths,
    [string[]]$Patterns
  )

  foreach ($path in $Paths) {
    foreach ($pattern in $Patterns) {
      if ($path -like $pattern) {
        return $true
      }
    }
  }
  return $false
}

function Get-ChangedPath {
  param([string[]]$Lines)

  $paths = @()
  foreach ($line in $Lines) {
    if ([string]::IsNullOrWhiteSpace($line)) {
      continue
    }

    $parts = $line -split "\s+"
    if ($parts.Count -gt 1) {
      $paths += $parts[$parts.Count - 1]
    }
  }
  return $paths
}

function New-CodexCommitMessage {
  param([string[]]$ChangedPaths)

  $hasNavigation = Test-AnyPath $ChangedPaths @(
    "components/FloatingMenu.tsx",
    "app/lib/floatingMenu*",
    "app/globals.css",
    "app/calendar/page.tsx",
    "app/today/page.tsx",
    "app/coach/page.tsx"
  )
  $hasLocation = Test-AnyPath $ChangedPaths @(
    "components/BirthDetailsForm.tsx",
    "app/lib/locations*"
  )
  $hasCodexHelper = Test-AnyPath $ChangedPaths @(
    "codex-commit-push.bat",
    "scripts/codex-commit-push.ps1",
    "README.md"
  )
  $hasLlmRetention = Test-AnyPath $ChangedPaths @(
    ".env.production.example",
    "app/services/llm_retention_client.py",
    "tests/test_llm_retention_client.py"
  )
  $hasBackend = Test-AnyPath $ChangedPaths @(
    "app/routers/*",
    "app/schemas/*",
    "app/services/*",
    "tests/*"
  )

  if ($hasNavigation -and $hasLocation -and $hasCodexHelper) {
    return "Improve navigation, location selection, and Codex workflow"
  }
  if ($hasNavigation -and $hasLocation) {
    return "Improve navigation and location selection"
  }
  if ($hasLlmRetention) {
    return "Update LLM retention provider support"
  }
  if ($hasCodexHelper) {
    return "Add Codex commit and push helper"
  }
  if ($hasNavigation) {
    return "Improve responsive navigation menu"
  }
  if ($hasLocation) {
    return "Improve birth location selection"
  }
  if ($hasBackend) {
    return "Update backend behavior"
  }
  if (Test-AnyPath $ChangedPaths @("docs/*", "*.md")) {
    return "Update documentation"
  }
  if (Test-AnyPath $ChangedPaths @("*.test.*", "tests/*")) {
    return "Update tests"
  }

  return "Update project files"
}

$repoRoot = (Read-Git @("rev-parse", "--show-toplevel") | Select-Object -First 1).Trim()
Set-Location $repoRoot

$branch = (Read-Git @("branch", "--show-current") | Select-Object -First 1).Trim()
if ([string]::IsNullOrWhiteSpace($branch)) {
  throw "Current HEAD is detached. Switch to a branch before committing."
}

$status = @(Read-Git @("status", "--porcelain"))
if ($status.Count -eq 0) {
  Write-Host "No changes to commit."
  exit 0
}

if ($DryRun) {
  $changedPaths = Get-ChangedPath $status
  $subject = if ([string]::IsNullOrWhiteSpace($Message)) {
    New-CodexCommitMessage $changedPaths
  } else {
    $Message
  }

  Write-Host "Repository: $repoRoot"
  Write-Host "Branch: $branch"
  Write-Host "Commit message: $subject"
  Write-Host "Changed files:"
  $status | ForEach-Object { Write-Host "  $_" }
  if ($NoPush) {
    Write-Host "Push: disabled"
  } else {
    $targetBranch = if ([string]::IsNullOrWhiteSpace($PushBranch)) { $branch } else { $PushBranch }
    Write-Host "Push target: $Remote HEAD:$targetBranch"
  }
  exit 0
}

Invoke-Git @("add", "-A")
Invoke-Git @("diff", "--cached", "--check")

$cachedLines = @(Read-Git @("diff", "--cached", "--name-status"))
if ($cachedLines.Count -eq 0) {
  Write-Host "No staged changes to commit."
  exit 0
}

$changedPathsForMessage = Get-ChangedPath $cachedLines
$commitMessage = if ([string]::IsNullOrWhiteSpace($Message)) {
  New-CodexCommitMessage $changedPathsForMessage
} else {
  $Message
}

Write-Host "Committing with message: $commitMessage"
Invoke-Git @("commit", "-m", $commitMessage)

if ($NoPush) {
  Write-Host "Commit created. Push skipped because -NoPush was set."
  exit 0
}

$targetBranchName = if ([string]::IsNullOrWhiteSpace($PushBranch)) { $branch } else { $PushBranch }
Write-Host "Pushing to $Remote HEAD:$targetBranchName"
if ([string]::IsNullOrWhiteSpace($PushBranch) -or $PushBranch -eq $branch) {
  Invoke-Git @("push", "--set-upstream", $Remote, "HEAD:$targetBranchName")
} else {
  Invoke-Git @("push", $Remote, "HEAD:$targetBranchName")
}
Invoke-Git @("ls-remote", "--heads", $Remote, $targetBranchName)
