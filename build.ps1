param(
    [string]$Task = "build",
    [string]$ArchFlags = "",
    [string]$Project = "canipy",
    [string]$SrcEntry = "main.py",
    [string]$ReqsTxt = "requirements.txt",
    [string]$PyInstArgs = "--onefile --noconsole",
    [int]$SkipDeps = 0
)

function Install-Deps {
    if (Test-Path $ReqsTxt) {
        Write-Host "Installing dependencies..."
        python -m pip install -r $ReqsTxt
    } else {
        Write-Host "No requirements.txt found, skipping!"
    }
}

function Publish-Project {
    Write-Host "Packaging CaniPy..."
    $argsArray = $PyInstArgs -split " "
    $archArray = $ArchFlags -split " "
    python -m PyInstaller @argsArray @archArray -n $Project $SrcEntry
}

function Clean-Build {
    Write-Host "Cleaning build artifacts..."
    Remove-Item -Recurse -Force "dist", "build", "$Project.spec" -ErrorAction SilentlyContinue
}

switch ($Task.ToLower()) {
    "build" {
        Publish-Project
        break
    }
    "deps" {
        Install-Deps
        break
    }
    "all" {
        Install-Deps
        Publish-Project
        break
    }
    "clean" {
        Clean-Build
        break
    }
    "rebuild" {
        Clean-Build
        if ($SkipDeps -eq 0) { Install-Deps }
        Publish-Project
        break
    }
    default {
        Write-Host "Unknown task: $Task" -ForegroundColor Red
        Write-Host "Available tasks: build, deps, all, clean, rebuild"
        break
    }
}
