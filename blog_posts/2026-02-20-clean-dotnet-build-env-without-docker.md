---
title: Abusing the .NET SDK for a fully configured environment in 0 commands
date: 2026-02-20
tags: [.NET]
---

There are a million different versions of .NET out there. The chance that you have the very specific right one when cloning a repository is minimal. While Docker attempted to solve this problem, it has its limitations. Wouldn't it be far better if NuGet sources and SDK versions could just work, like they do in other ecosystems? 

With the method described below, you can make sure developers can build and run your .NET Core project without any faff to resolve dependencies, so long as they have the .NET SDK version 6 or later.  

## Skipping NuGet restore against redundant sources 

If you use any private NuGet sources, you're probably familiar with the endless cycle. Your restore fails due to a permissions or mapping error, you run `dotnet nuget list source`, `dotnet nuget disable source CompanyInternal`, `dotnet nuget enable source CompanyInternal`, repeat ad infinitum. 

Great news: it doesn't have to be like this! You can use the [nuget.config](https://learn.microsoft.com/en-us/nuget/reference/nuget-config-file) file to configure NuGet sources at the repository level, which prevents users from calling out to redundant private sources and make sure that all the sources you *are* using are available and enabled. 

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <clear />
    <add key="nuget" value="https://api.nuget.org/v3/index.json" />
  </packageSources>
  <disabledPackageSources>
    <clear />
  </disabledPackageSources>
</configuration>
```

>[!TIP]
> If you're using multiple sources, you can also use nuget.config to configure package source mapping for a performance boost (and to be kinder to your sources!)

## Listing the SDK(s) you want

Modern versions of the .NET CLI recognise a file called "[global.json](https://learn.microsoft.com/en-us/dotnet/core/tools/global-json
)", which defines which SDK version(s) are valid in the current directory and causes the dotnet command to fail if it doesn't have the right one. 

Since we just want the information from here, and not the protection against running commands (which would shoot us in the foot later on), we'll define all the SDKs we need in files `/sdk/*.json`. Because we'll be using this information to install the SDK later on, you'll need to use a version number that exactly matches a released version in major, minor, and patch. 

Say a project relies on the .NET 10 SDK - we can add the following to `/sdk/net10.0.100.json`. 

```json
{
  "sdk": {
    "version": "10.0.100",
    "rollForward": "disable"
  }
}
```

## Listing the tools you want 

In the file `.config/dotnet-tools.json` (known as the [tool manifest](https://learn.microsoft.com/en-us/dotnet/core/tools/local-tools-how-to-use)), we can define a list of tools we recommend for a repository. This file can be created automatically using `dotnet new tool-manifest`, and will be automatically updated when running `dotnet tool` commands. 

We're going to need [cake](https://cakebuild.net/) (`dotnet tool install cake.tool`), a build system for .NET conceptually inspired by make, with the twist that it's configured in C#. Once it's installed, the tool manifest should look like this: 

```json
{
  "version": 1,
  "isRoot": true,
  "tools": {
    "cake.tool": {
      "version": "5.1.0",
      "commands": [
        "dotnet-cake"
      ],
      "rollForward": false
    }
  }
}
```

## Putting it all together... 

Putting together everything we've learned so far, we can build a cake target that uses the official [dotnet install scripts](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-install-script) to automatically download the required SDKs onto our system. If running on MacOS or Linux with the GPG command available, we can also perform a checksum on the script we download. 

The following script, which should live in `build.cake`, will automatically install every SDK defined in `/sdk/*.json`. It's compatible with Windows, MacOS, and Linux, and will verify file integrity using GPG when available. 

```csharp
var target = Argument("target", "InstallSdk");

Task("InstallSdk").Does(() =>
{
    var sdkFiles = GetFiles("./sdk/*.json").ToList();

    if (!sdkFiles.Any())
        return;

    if (IsRunningOnWindows())
    {
        var scriptFile = File("./dotnet-install.ps1");

        try
        {
            DownloadFile("https://dot.net/v1/dotnet-install.ps1", scriptFile);

            foreach (var sdkFile in sdkFiles)
                StartProcess("pwsh", 
                    new ProcessSettings { Arguments = $"-ExecutionPolicy Bypass -File \"{MakeAbsolute(scriptFile)}\" --jsonfile \"{sdkFile}\"" });
        }
        finally
        {
            if (FileExists(scriptFile))
                DeleteFile(scriptFile);
        }
    }
    else
    {
        var scriptFile = File("./dotnet-install.sh");
        var ascFile = File("./dotnet-install.asc");
        var sigFile = File("./dotnet-install.sig");

        try
        {
            DownloadFile("https://dot.net/v1/dotnet-install.sh", scriptFile);

            if (Context.Tools.Resolve("gpg") != null)
            {
                DownloadFile("https://dot.net/v1/dotnet-install.asc", ascFile);
                DownloadFile("https://dot.net/v1/dotnet-install.sig", sigFile);

                StartProcess("gpg",
                    new ProcessSettings { Arguments = $"--import \"{MakeAbsolute(ascFile)}\"" });

                var exitCode = StartProcess("gpg",
                    new ProcessSettings { Arguments = $"--verify \"{MakeAbsolute(sigFile)}\" \"{MakeAbsolute(scriptFile)}\"" });

                if (exitCode != 0)
                    throw new CakeException("The dotnet install script failed the GPG integrity check.");
            }

            foreach (var sdkFile in sdkFiles)
                StartProcess("/bin/bash", new ProcessSettings{ Arguments = $"\"{MakeAbsolute(scriptFile)}\" --jsonfile \"{sdkFile}\"" });
        }
        finally
        {
            if (FileExists(scriptFile))DeleteFile(scriptFile);
            if (FileExists(ascFile)) DeleteFile(ascFile);
            if (FileExists(sigFile)) DeleteFile(sigFile);
        }
    }
});

RunTarget(target);
```

To run this, we'll use `dotnet tool restore` to ensure cake is installed (with nuget.config ensuring that it's discoverable), then `dotnet cake --target InstallSdk` to install the SDK(s). 

## But didn't I promise 0 commands? 

It might be a bit much to expect every developer to read the file which is &lt;sarcasm&gt;so confusingly&lt;/sarcasm&gt; named README.md and follow the simple instructions therein. It's easier if we just have our SDK restore happen automatically when the user needs it. 

We can hook into the MSBuild compiler pipeline by defining a custom target. The below one, which should be placed in file `Directory.Build.targets`, will cause our cake restore to run before build. It'll only run for the project that was specifically named to be built, and only once (adding a cache file in the project's `obj` folder to speed up subsequent builds). 

```xml
<Project>
    <Target Name="PreBootstrapSdk"
        BeforeTargets="PrepareForBuild"
        Condition="
  '$(MSBuildProjectFullPath)' == '$(MSBuildProjectFullPath)' 
  AND '$(IsCrossTargetingBuild)' != 'true'
  AND '$(BuildingProject)' == 'true'
  AND !Exists('$(BaseIntermediateOutputPath)prebootstrap.cache')">

    <PropertyGroup>
      <RepoRoot>$(MSBuildThisFileDirectory)</RepoRoot>
    </PropertyGroup>

    <MakeDir Directories="$(BaseIntermediateOutputPath)" />

    <Exec Command="dotnet tool restore"
          WorkingDirectory="$(RepoRoot)" />

    <Exec Command="dotnet cake --target InstallSdk"
          WorkingDirectory="$(RepoRoot)" />

    <WriteLinesToFile
        File="$(BaseIntermediateOutputPath)prebootstrap.cache"
        Lines="done"
        Overwrite="true" />

    </Target>
</Project>
```

## Security considerations

Strictly speaking, we're running code that the user might not expect to run. It's curteous to be up-front about the fact that you're doing this in your README so as not to scare unwitting developers. 

The way we're using the install scripts here is basically the cake equivalent of `curl | sh` (or `irm | iex` for Windows users): downloading code from the internet and running it without checking what it does. While the GPG check provides an added layer of assurance, you might want to download the install scripts into your repo for an absolute guarantee of security (and to reduce network traffic, which is always a good thing). 

Finally, be wary of running nuget auth commands while under the scope of a local nuget.config file. If you're not careful, you could end up committing a personal secret. 

## Afterword 

By combining many niche and useful aspects of the .NET SDK with a simple cake build script, we've guaranteed that any developer who clones your repo should be able to get started effortlessly while having to do nothing more than their usual build/run workflow. 

## References 

https://learn.microsoft.com/en-us/nuget/reference/nuget-config-file

https://learn.microsoft.com/en-us/dotnet/core/tools/global-json

https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-install-script

https://learn.microsoft.com/en-us/dotnet/core/tools/local-tools-how-to-use

https://cakebuild.net/