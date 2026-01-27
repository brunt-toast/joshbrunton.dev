---
title: How to Sign a .NET MAUI App Targeting Windows
date: 2026-01-28
tags: [.NET, MAUI, tutorial]
---

## Disclaimer 

This article was proofread by GPT 5o, and some spelling corrections were made as a result. The writing and technical information were not generated or influenced by any LLM. 

## Preamble

The process for publishing a .NET MAUI app for Windows is arcane and convoluted. Visual Studio's publishing wizard, which used to simplify it into a few easy steps, has become fragile and outdated, and the documentation on how to do it by hand is fragmented and conflicting. 

This article breaks the signing and publishing process down into easy-to-follow steps, explaining the "why" as well as the "how" as we go. By the end, you should have the knowledge to build a PowerShell script or CI pipeline to sign and pack your app in a single command, and optionally publish it to the Microsoft Store. 

This method has been figured out from scratch via experimentation, without significant help from documentation. It's been tried and tested against .NET 9 and 10 apps, the minimum supported versions at time of writing on Tuesday 28<sup>th</sup> January, 2026, and targeting the Windows SDK version 10.0.19041.0. Both plain MAUI and Blazor Hybrid apps have been tested, and the process is identical between them. 

## Requirements 

You'll need a Windows machine with the appropriate .NET SDK for your project. While MacOS and Linux machines can sometimes be made to work, Windows is practically required because of its MSIX tooling. 

The examples here use PowerShell, with cmdlets from the PKI (Public Key Infrastructure) module. These cmdlets are usually available by default, but if they're not, you can check that the module is available using `Get-Module -ListAvailable -Name PKI`, and import it using `Import-Module -Name PKI`. 

Finally, if you want to submit your app to the Microsoft Store, you'll need access to the Microsoft Partner Center at https://partner.microsoft.com/en-GB/. 

## MAUI &amp; Windows Versioning 

Versioning MAUI Windows apps is slightly convoluted. The Windows app identity's version isn't inherited from the assembly version or MAUI appplication display version; instead, it's defiend in the line `<Identity ... Version="0.0.0.0" />`, in the file `Platforms/Windows/Package.appxmanifest`. This value won't affect the assembly or display version in your app, only the resultant .msix file's version. 

If publishing to the Microsoft Store, note that the Windows app identity version must *always* go up, because the store won't accept a downgrade, and that the fourth place is assigned by the store and shouldn't be used by the developer. 

## Getting a Publisher ID 

If you only plan on side-loading your app, you can skip over this step. The publisher ID is only checked by the Microsoft Store, so it won't affect side-loaded installation. 

If you want to submit to the Microsoft store, you'll need a valid publisher ID, which means you'll need to be a registered Microsoft Partner. In Partner Center, go to **Settings &gt; Account Settings &gt; Identifiers**, then select the "Windows" tab. You should see your Windows publisher ID here, in the form `CN=00000000-0000-0000-0000-000000000000`. 

## Generating a Certificate 

You'll need to generate a self-signed certificate with certain properties. It must be an exportable code-signing certificate with a specific subject and text extension. 

Ideally, you'll generate and export a certificate only once, and keep the same one throughout the lifetime of your application. The Microsoft Store will only use this certificate for identity validation against your Publisher ID and will re-sign your package with its own certificates, but a side-loaded app should keep the same certificate over multiple versions to streamline the installation and update process. 

The type of the certificate must be `CodeSigningCert`. Under the hood, this sets the certificate's Enhanced Key Usage (EKU) property to the value `1.3.6.1.5.5.7.3.3`. 

If you plan to publish to the Microsoft Store, the subject must be the same as your identity's publisher, found in `MauiAppDir/Platforms/Windows/Package.appxmanifest` as an attribute on the `<Identity ... />` element. Generally this should be in the form `CN=00000000-0000-0000-0000-000000000000`, which is the publisher ID retrieved from the Partner Center. If you're only planning on side-loading, the subject isn't important, and can be set to whatever you want.

You'll also need the text extension to be `2.5.29.19={text}false` (where `{text}` is a literal, not interpolated.) This sets the "basic constraints" of the certificate, a concept in X.509 which describes whether the certificate is allowed to act as a certificate authority (CA), and if so, how deep the certification chain may be. In our case, we're saying that "Subject Type=End Entity", meaning that this certificate is *not* an authority, and that as a result, "Path Length Constraint=None", meaning that the path length constraint is not relevant. 

To quickly generate a new self-signed certificate with these parameters, you can use the following PowerShell snippet.

```powershell
$subject = "CN=00000000-0000-0000-0000-000000000000"

$cert = New-SelfSignedCertificate `
  -Type CodeSigningCert `
  -Subject "${subject}" `
  -CertStoreLocation "Cert:\CurrentUser\My" `
  -KeyExportPolicy Exportable `
  -KeySpec Signature `
  -KeyLength 2048 `
  -HashAlgorithm SHA256 `
  -TextExtension @("2.5.29.19={text}false")
```

For added security, you can set the KeyLength to 4096 (both 2048 and 4096 are considered acceptable by the Microsoft Store), and add an expiry date by adding `-NotAfter (Get-Date).AddYears(10)`. Long periods are best since expiry will prevent upgrades and reinstallations for side-loaded apps. 

## Exporting a Certificate as PFX 

PFX (personal information exchange) is a password protected file format which holds both a certificate and its corresponding private key. 

You'll need to export the certificate you just generated in the PFX format in order to sign your app. You can do so with the following PowerShell snippet. We'll be referencing the variables `$subject` and `$cert` from the last snippet, so make sure they're still in context. 

Note that you'll need to set the variable `$password` yourself - you're setting it for the first time here, so it can be anything you want, but for security you should always use a secure, unique, and randomly generated password. 

You'll also need to make sure the directory you're trying to export to actually exists, which we do here before exporting. It's recommended to use an absolute path outside of your repository, so you can reference it without considering the current directory and you don't risk accidentally committing it to version control. 

```powershell
$password = Read-Host "Enter PFX password" -AsSecureString

Test-Path C:\Cert || mkdir C:\Cert

Export-PfxCertificate `
  -Cert $cert `
  -FilePath "C:\Cert\${subject}.pfx" `
  -Password ${password}
```

## Retrieving the Thumbprint 

To identify the certificate you just made, you'll need to grab its thumbprint. The thumbprint is a hash of the whole certificate, which is considered its unique identifier (since certificates don't have to be unique by subject). 

To get the thumbprint, you can use the following PowerShell snippet. Again we'll be referencing `$subject` and `$password` from previous snippets. 

```powershell
$tp = Import-PfxCertificate -FilePath "C:\Cert\${subject}.pfx" `
	-CertStoreLocation Cert:\CurrentUser\My `
	-Password "${password}" | Select-Object -ExpandProperty Thumbprint
```

## Storing Certificate Details

You should keep your certificate and its details (password and thumbprint) in a secure place. Many build pipeline services offer a place to securely store files and variables, which can then be referenced from inside the pipeline without having been committed to version control. You should also back up your certificates in a secure place locally. 

Even though a .pfx file is password-protected, and even if your repository is private, you should never commit your certificate or password to version control. 

## Signing Your Build 

To build a signed msix package, MSBuild needs 7 specific properties. Each property *can* be stored as a child of a PropertyGroup, but some shouldn't for security reasons. In this example, we'll be using MSBuild switches (`/p:Key="Value"`) for all of them, so as not to complicate things in case the project file has other values for the relevant keys. 

We'll use the `dotnet publish` command to publish our app. We'll have to give it a path to our project, as well as setting the Release configuration (for optimisation) and the target framework (which you can find under `<TargetFrameworks>` in a PropertyGroup in your project file - for the Windows SDK, it's not just your .NET version.) 

To convince it to give us an MSIX file (a Windows installable), we'll need to set a few related properties: 

* `WindowsPackageType="MSIX"` 
* `EnableMsixTooling="true"`
* `GenerateAppxPackageOnBuild="true"`. 

To tell it about our signing certificate, we'll need to set the following (make sure you have the variables `$pfxFilePath`, `$password` and `$tp` available).

* `AppxPackageSigningEnabled="true"`
* `PackageCertificateKeyFile="${pfxFilePath}"`
* `PackageCertificatePassword="${password}"`
* `PackageCertificateThumbprint="${tp}"`

All of this comes together to make a single dotnet publish command: 

```powershell
$project = "./path/to/your.csproj"

dotnet publish "${project}" `
	-c Release `
	-f net10.0-windows10.0.19041.0 `
  
  /p:WindowsPackageType="MSIX" `
  /p:EnableMsixTooling="true" `
  /p:GenerateAppxPackageOnBuild="true" `

  /p:AppxPackageSigningEnabled="true" `
	/p:PackageCertificateKeyFile="${pfxFilePath}" `
	/p:PackageCertificatePassword="${password}" `
	/p:PackageCertificateThumbprint="${tp}"
```

You may also need to specifically set the runtime identifier. For .NET 9 and below, this is done with `-r win10-x64`; for .NET 10 and above, it's `-r win-x64`. 

## Retrieving The Signed Installer 

By default, the built package will be written to `${csProjDirectory}/bin/Release/${targetFramework}/${rid}/AppPackages/${AssemblyName}_${appxVersion}_Test`. 

If it's not here, check that you haven't diverted build output in your project file, or with `Directory.Build.props` or `Directory.Build.targets` files. 

## Testing The Signed Installer

You can test that your signing has worked by uninstalling any existing versions of your app, then running the `Install.ps1` script in the app packages directory. You should be prompted to trust the certificate, which may require administrator consent. If this works, the app should continue to install, and you'll know that the signing was successful. 

Some environments will block the PowerShell script depending on execution policy, so alternatively, you can double-click the .cer file to trust it, then double-click the .msix file to run the installer. 

If the signing was unsuccessful, Windows won't let you install the app. 

## Deploying The App

If you're sending the package off to the Microsoft Store, you'll just need the .msix file in the app package directory. 

If your users will be sideloading the app, you'll need to deliver the .msix file and the .cer file as the bare minimum, but ideally you should send off the whole directory. 
