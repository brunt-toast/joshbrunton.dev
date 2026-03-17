---
title: Authenticating with custom NuGet sources in terminals and pipelines
date: 2026-02-18
tags: [.NET, NuGet, Windows, MacOS, Linux]
---

In a graphical environment, it's easy to authenticate with a custom NuGet source. With the appropriate artifacts provider, like [this one for Azure DevOps](https://github.com/microsoft/artifacts-credprovider), a simple `dotnet restore --interactive` will present a login prompt for the relevant platform and generate an access token. 

In CLI environments such as build pipelines or some servers, it's not quite so simple. Authentication must be set up a little more manually. 

## Generate an access token

First, you'll need to generate a personal access token (PAT). While some NuGet sources also support using a plaintext password, a PAT is more secure. 

For Azure DevOps, go to https://myorg.visualstudio.com/_usersSettings/tokens, click "New Token", and generate a token for the relevant organisation with the "Packaging.Read" scope (or above, if you intend to publish to or manage the source). Save the generated token, because it will never be presented again!

## Add credentials to NuGet.Config

The easiest way to do add credentials to a config is with the dotnet CLI. 

>[!Warning]
> **Don't run the command to store your username and password when you're under a local nuget.config's perview!** This can cause the credentials to be saved in the repository, which is a security risk. To be sure, you might want to `cd ~` first.
 
```bash
dotnet nuget add source \
    'https://myorg.pkgs.visualstudio.com/_packaging/My.Packages/nuget/v3/index.json' \
    --name 'My.Packages' \
    --username 'someone@example.com' \
    --password 'SuperSecretToken' 
```

>[!NOTE]
> If you're not on Windows, you'll also need to add `--store-password-in-clear-text`. This is because encryption isn't supported on non-Windows platforms.

Alternatively, you can add your credentials to your config manually by editing your nuget config file. The location of the config is dependent on your platform: 

<table>
<thead>
<tr>
<th>Platform</th>
<th>Location</th>
</tr>
</thead>
<tbody>
<tr>
<td>Windows</td>
<td><code>%APPDATA%\NuGet\NuGet.Config</code></td>
</tr>
<tr>
<td>MacOS</td>
<td rowspan="2"><code>~/.config/NuGet/config/*.config</code> or <code>~/.nuget/config/*.config</code></td>
</tr>
<tr>
<td>Linux</td>
</tr>
</tbody>
</table>


In some cases, you might want to add it to the computer-level config, which is located at:
| Platform | Location |
|---|---|
| Windows | `%ProgramFiles(x86)%\NuGet\Config\NuGet.Config` |
| MacOS |  `/Library/Application Support/NuGet.Config` |
| Linux | `/etc/opt/NuGet/Config/NuGet.Config` |

The following snippet shows the structure of the file. 

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <add key="My.Packages" value="https://myorg.pkgs.visualstudio.com/_packaging/My.Packages/nuget/v3/index.json" />
  </packageSources>
  <packageSourceCredentials>
    <My.Packages>
      <add key="Username" value="someone@example.com" />
      <add key="ClearTextPassword" value="SuperSecretToken" />
    </My.Packages>
  </packageSourceCredentials>
</configuration>
```

## Usage 

That's all! There's no need to explicitly inherit this configuration in a repository-level nuget.config, so long as the package source names are identical. Restores should start working like magic. 

## Security Consideration

As previously mentioned, you probably don't want to store your credentials in a repository-level nuget.config. Even if access to your repo is synonymous with access to your nuget source, sharing your personal credentials in this way can compromise the chain of custody in the event of a security incident.

No matter which method you use, be wary that these credentials are stored in your user-level NuGet.Config file. If you share your home folder, e.g. by backing up dotfiles to a public Git repository, know that your NuGet.Config file contains privileged information and should be ignored. 

If your password or token is ever committed to a repo, even if you haven't pushed it, you should change your password / invalidate your token immediately. 