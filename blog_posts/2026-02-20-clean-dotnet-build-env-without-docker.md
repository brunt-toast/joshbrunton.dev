---
title: A clean .NET build environment without Docker
date: 2026-02-20
tags: [.NET, NuGet]
---

Docker is a great tool to mitigate the "it works on my machine" problem, but it can be slow, heavy, and confusing, especially when developing for web when certificates are required. 

This post details how to set up a consistent .NET build environment, starting with only the `dotnet` command you already have. 

## Managing SDK versions 

The varying SDK versions get confusing fast. It's unduly common to have to dig through a repository for all the SDK versions used, then search around the internet to install those versions, and finally select the right one to build the startup project. 

Since the .NET Core 3.1 SDK, the dotnet command recognises a config file called global.json. One purpose of this file is to declare the valid SDK version(s) for a directory. 

Let's say you want to build using .NET 10.0.100 exactly. In your global.json file, you can write: 
```json
{
  "sdk": {
    "version": "8.0.300",
    "rollForward": "latestFeature"
  }
}
```

This is limited to one declaration per global.json file, so mileage may vary for projects with multiple targets. 

## Installing SDK versions 

So long as the specific named SDK version in global.json actually exists, you don't need to track it down manually among the hundreds of SDK versions online. You can use the dotnet install scripts to do the work for you. 

First, download the latest version of the install script, from https://dot.net/v1/dotnet-install.ps1 (Windows) or https://dot.net/v1/dotnet-install.sh (MacOS &amp; Linux). Then, run the script with the arguments `--jsonfile ./global.json`. This will automatically install the named version and make it available globally on the system. 

This seems like we've strayed a little bit outside the .NET command alone, but don't worry, we'll get back to that later (and there will be cake!)

## Manage NuGet sources 

If you've ever worked with a private NuGet source, you might know the pain of having to authenticate with or disable a source to get something to work. The nuget.config file can address exactly that problem. 

If you've ever used nuget before - which, chances are, you have - you'll already have a user and perhaps a system configuration. The following table shows where they're located: 

| OS | Scope | Path |
| --- | --- | --- |
| Windows | User  | %APPDATA%\NuGet\NuGet.Config |
| Windows | Computer | %ProgramFiles(x86)%\NuGet\Config |
| MacOS | User | ~/.config/NuGet/NuGet.Config (mono) ~/.nuget/NuGet/NuGet.Config (dotnet) |
| MacOS | Computer | /Library/ApplicationSupport or $NUGET_COMMON_APPLICATION_DATA/ |
| Linux | User | ~/.config/NuGet/NuGet.Config (mono) or ~/.nuget/NuGet/NuGet.Config (dotnet)  |
| Linux | Computer | /etc/opt/NuGet/Config or $NUGET_COMMON_APPLICATION_DATA/  |

Since nuget config is inherited, we'll need to start with a blank slate in our repository's nuget.config by clearing our existing package sources. 

```xml
<packageSources>
    <clear />
</packageSources>
```

Next up, we can add the sources we actually want to use: 

```xml
<packageSources>
    <clear />
    <add key="nuget" value="https://api.nuget.org/v3/index.json" />
</packageSources>
```

And make sure they're enabled, even if they're disabled at a higher level. 

```xml
<disabledPackageSources>
    <clear />
</disabledPackageSources>
```

We can improve performance by reducing the number of redundant calls made using package source mapping: 

```xml
<packageSourceMapping>
    <packageSource key="nuget">
        <package pattern="*" />
    </packageSource>
</packageSourceMapping>
```

And, if security is not a concern, add credentials for custom package sources. 

```xml
<packageSourceCredentials>
    <My.Packages>
        <add key="Username" value="someone@example.com" />
        <add key="ClearTextPassword" value="SuperSecretToken" />
    </My.Packages>
</packageSourceCredentials>
```

With all this, we have complete control over the available and enabled NuGet sources for our repository. 

## Managing and installing dotnet tools 

.NET tools are NuGet packages that contain a program that can be invoked from the command line. `dotnet-ef` is a particularly popular one, used for interacting with the Entity Framework ORM. 

You can recommend tools in your repository by using the tool manifest, a JSON file describing names and versions of dotnet tools. 

You can create a manifest by using `dotnet new tool-manifest`, or by manually creating the file `.config/dotnet-tools.json` with the following content: 

```json
{
  "version": 1,
  "isRoot": true,
  "tools": {}
}
```

Then, any time you use `dotnet tool install`, the installed tool will be added to the config. After running `dotnet tool install dotnet-ef`, the manifest would look like: 

```json
{
  "version": 1,
  "isRoot": true,
  "tools": {
    "dotnet-ef": {
      "version": "10.0.3",
      "commands": [
        "dotnet-ef"
      ],
      "rollForward": false
    }
  }
}
```

You can quickly install all tools in a manifest by using the command `dotnet tool restore`. 

## Build scripts using Cake 

The most popular dotnet tool on nuget.org is Cake, a build automation system inspired by GNU Make. You can install it using `dotnet tool install cake.tool`. You may also want to use `dotnet new install Cake.Template` for the cakefile template - if you do, you can create a cakefile using `dotnet new cakefile`. 

The specifics of the cakefile are far too much to get into here, so check out the [Getting Started docs](https://cakebuild.net/docs/getting-started/setting-up-a-new-cakesdk-project). 

You may, however, want to include the following target, which will automatically install the .NET SDK required by global.json as described earlier. Additional code is included to perform a checksum on the install script if GPG is available, since running a shell script from the internet without manually checking its contents is a risky move. Note that PowerShell will refuse to run any file that doesn't have a .ps1 extension, so if the task fails on Windows, the powershell script will persist and may be accidentally added to version control if not careful.

```csharp
Task("InstallSdk").Does(() =>
{
    var sdkFiles = GetFiles("./**/*.sdk.json")
        .Concat(GetFiles("./**/sdk.json"))
        .Distinct()
        .ToList();

    if (!sdkFiles.Any())
    {
        return;
    }

    if (IsRunningOnWindows())
    {
        var scriptFile = File("./dotnet-install.ps1");

        try
        {
            DownloadFile("https://dot.net/v1/dotnet-install.ps1", scriptFile);

            foreach (var sdkFile in sdkFiles)
            {
                StartProcess("pwsh", 
                    new ProcessSettings { Arguments = $"-ExecutionPolicy Bypass -File \"{MakeAbsolute(scriptFile)}\" --jsonfile \"{sdkFile}\"" });
            }
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
```

In Directory.Build.targets
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