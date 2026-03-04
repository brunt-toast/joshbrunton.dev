---
title: Framework-agnostic internationalization in .NET 
date: 2026-03-04
tags: [.NET]
---

If your app is marketed towards users in multiple countries, you might want to add translations for user-facing content in your app. Microsoft.Extensions.Localization makes this easy. 

## Package Reference

You'll need to reference the Microsoft.Extensions.Localization nuget package. 

```xml
<PackageReference Include="Microsoft.Extensions.Localization" Version="10.0.3" />
```

## Defining translations

First, define your default culture's resources. Under the folder `/Resource/Languages`, create a file with the `.resx` extensions. 

Set its build action to "Embedded Resource" and set the custom tool to ResX file code generator. If you're not using Visual Studio, you can do this manually in your project file like so: 

```xml
  <ItemGroup>
    <EmbeddedResource Update="Resources\Languages\MyComponentResources.resx">
      <Generator>ResXFileCodeGenerator</Generator>
      <LastGenOutput>MyComponentResources.Designer.cs</LastGenOutput>
    </EmbeddedResource>
  </ItemGroup>

  <ItemGroup>
    <Compile Update="Resources\Languages\MyComponentResources.Designer.cs">
      <DesignTime>True</DesignTime>
      <AutoGen>True</AutoGen>
      <DependentUpon>MyComponentResources.resx</DependentUpon>
    </Compile>
  </ItemGroup>
```

Note that a class will be generated from every .resx file at design time. For this reason, it's common to name them `*Resources.resx` (e.g. `MyComponentResources.resx`), so as not to confuse them with the existing classes. 

Alternatively, you can use this snippet, which will apply to all files in /Resources/Languages, but doesn't generate the Designer.cs files at design time, breaking IDE support. 

```xml
  <ItemGroup>
    <EmbeddedResource Update="Resources\Languages\*.resx">
      <Generator>MSBuild:Compile</Generator>
      <StronglyTypedFileName>$(IntermediateOutputPath)%(Filename).Designer.cs</StronglyTypedFileName>
      <StronglyTypedLanguage>CSharp</StronglyTypedLanguage>
      <StronglyTypedNamespace>$(RootNamespace).Resources.Languages</StronglyTypedNamespace>
      <StronglyTypedClassName>%(Filename)</StronglyTypedClassName>
    </EmbeddedResource>
  </ItemGroup>
```

The initial content of the file is a lot, but don't worry, you don't have to read or modify any of it. 

```xml
<?xml version="1.0" encoding="utf-8"?>
<root>
  <xsd:schema id="root" xmlns="" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:msdata="urn:schemas-microsoft-com:xml-msdata">
    <xsd:import namespace="http://www.w3.org/XML/1998/namespace" />
    <xsd:element name="root" msdata:IsDataSet="true">
      <xsd:complexType>
        <xsd:choice maxOccurs="unbounded">
          <xsd:element name="metadata">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="value" type="xsd:string" minOccurs="0" />
              </xsd:sequence>
              <xsd:attribute name="name" use="required" type="xsd:string" />
              <xsd:attribute name="type" type="xsd:string" />
              <xsd:attribute name="mimetype" type="xsd:string" />
              <xsd:attribute ref="xml:space" />
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="assembly">
            <xsd:complexType>
              <xsd:attribute name="alias" type="xsd:string" />
              <xsd:attribute name="name" type="xsd:string" />
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="data">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="value" type="xsd:string" minOccurs="0" msdata:Ordinal="1" />
                <xsd:element name="comment" type="xsd:string" minOccurs="0" msdata:Ordinal="2" />
              </xsd:sequence>
              <xsd:attribute name="name" type="xsd:string" use="required" msdata:Ordinal="1" />
              <xsd:attribute name="type" type="xsd:string" msdata:Ordinal="3" />
              <xsd:attribute name="mimetype" type="xsd:string" msdata:Ordinal="4" />
              <xsd:attribute ref="xml:space" />
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="resheader">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="value" type="xsd:string" minOccurs="0" msdata:Ordinal="1" />
              </xsd:sequence>
              <xsd:attribute name="name" type="xsd:string" use="required" />
            </xsd:complexType>
          </xsd:element>
        </xsd:choice>
      </xsd:complexType>
    </xsd:element>
  </xsd:schema>
  <resheader name="resmimetype">
    <value>text/microsoft-resx</value>
  </resheader>
  <resheader name="version">
    <value>2.0</value>
  </resheader>
  <resheader name="reader">
    <value>System.Resources.ResXResourceReader, System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089</value>
  </resheader>
  <resheader name="writer">
    <value>System.Resources.ResXResourceWriter, System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089</value>
  </resheader>
</root>
```

To add resources, add the following. 

```diff
  </resheader>
+ <data name="KeyToReference" xml:space="preserve">
+    <value>Text that will be shown</value>
+ </data>
</root>
```

To add an alternative culture, create another file with the same name, but with its ISO 639 Alpha 2 language code between the name and the extension. For example, `MyComponentResources.resx` adapted for metropolitan French (`fr`) would become `MyComponentResources.fr.resx`. The file is structured exactly the same - the only thing that should differ is the values. 

```diff
  </resheader>
+ <data name="KeyToReference" xml:space="preserve">
+    <value>Texte qui sera montré</value>
+ </data>
</root>
```

## Tip: File Nesting 

The number of resx files in your project should be equal to the number of supported cultures multiplied by the number of resource classes. This number can grow quickly. To make it more manageable, you can configure file nesting in your editor to group by the resource class. 

In VSCode, under `.vscode/settings.json`, add the following

```json
"explorer.fileNesting.enabled": true,
"explorer.fileNesting.expand": false,
"explorer.fileNesting.patterns": {
    "*.resx": "${capture}.*.resx",
}
```

For Visual Studio, it's a little more verbose, as there are no patterns or capture groups. In `.filenesting.json`: 
```jsonc
{
  "root": false,
  "dependentFileProviders": {
    "add": {
      "extensionToExtension": {
        "add": {
          ".fr.resx": [ ".resx" ],
          ".es.resx": [ ".resx" ],
          // more languages here...
        }
      }
    }
  }
}
```

## Using translations 

Using a simple translation is as simple as referencing the static string property on your resource class, e.g. `MyComponentResources.KeyToReference`. The getter will automatically resolve which culture to use. 

Note that if the value is empty or undefined, the resolver will fall back to the default culture. 

## Parameterised translations 

Not all languages put the same words in the same position. Sometimes, you need to interpolate a value into an indeterminate position in a localised resource. 

To use parameterised translation, you'll need to add localisation services to your dependency injection container. Thanks to the NuGet package we installed earlier, it's as simple as: 

```csharp
builder.Services.AddLocalization();
```

Then, wherever you want to use it, inject a `Microsoft.Extensions.Localization.IStringLocalizer<out T>`, where `T` is the name of your resx file with a namespace generated from the path, e.g. `Resources.Languages.MyComponentResources`.

In your resource declaration, use `{0}` (with incrementing numbers) in the declaration, then add additional parameters to the indexer used to access the resource. 

For example, in our resource definitions: 
* `en`: FileLocation = "You can find the file at {0}.";
* `ja`: FileLocation = "ファイルは{0}で見つかります。";

Finally, use an indexer on the IStringLocalizer, with the resource key and any parameters. `_l10nService[MyComponentResources.FileLocation, fileLocation]` will become: 

* `en`: "You can find the file at C:\Users\User\Documents."
* `ja`: ファイルはC:\Users\User\Documentsで見つかります。

## Changing cultures at runtime 

To change the culture at runtime, modify the properties on `System.Globalization.CultureInfo` for the culture you want. Note that you may need to trigger a re-render of the UI to update all resource strings. 

```csharp
var culture = new CultureInfo("de-DE");
CultureInfo.DefaultThreadCurrentCulture = culture;
CultureInfo.DefaultThreadCurrentUICulture = culture;
```
