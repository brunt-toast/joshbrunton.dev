Managing configuration is surprisingly difficult to get right. Most solutions implemented by hand fall short in some way, including: 
* Locking resources 
* Introducing performance issues by polling sources for every read 
* Necessitating restarts to change config

But, `Microsoft.Extensions.Configuration` solves these problems for you, if you know how to use it correctly. 

To get the most out of this, you'll need a basic understanding of dependency injection and the 
hosting model. 

## Getting Started

First, you'll need to ensure you have the NuGet package `Microsoft.Extensions.Hosting` installed. This comes transiently with many project types, including ASP.NET APIs, Blazor apps, and .NET MAUI apps. An app that is correctly configured for hosting will have an entry point that looks something like this: 

```csharp
var builder = WebApplication.CreateBuilder(); 
// ... 
var app = builder.Build();
// ...
app.Run();
```

## Adding sources

Some host builders will automatically include certain configuration sources. For example, the WebApplicationBuilder automatically brings in appsettings.json, environment variables, and user secrets. 

If you want to add another configuration source, you can install a NuGet package for it. `Microsoft.Extensions.Configuration.*` provide a variety of sources. The below example uses `Tomlyn.Extensions.Configuration` to include a `config.toml` file: 

```csharp
builder.Configuration.AddTomlFile("config.toml");
```

By default, the builder will error if the source is missing. Most methoods like this allow consumers to add argument `optional` (default: `false`) to change this. You can also add `reloadOnChange` (default: `false`) to most calls like this.

## Registering option types

Often, you'll want your options to be richly typed, so you don't have to call `IConfiguration.GetSection(...)` and use magic strings everywhere. To map a section of configuration to an options type, use the following: 

```csharp
IConfigurationSection section = builder.Configuration.GetSection(MyOptions.ConfigurationSectionName);
builder.Services.Configure<MyOptions>(section);
```

>[!TIP]
> Keep the name of the config section in a `public const string` on the options type to make it easy to discover the names for each section. 

>[!NOTE]
> The path separator for `IConfigurationSection.GetSection(string)` is `:`. For example, the section `{"Auth": {"Providers": {"Azure": {/*...*/}}}}` would be referred to as `Auth:Providers:Azure`. 

## Using static configuration

For options that are tied to the lifetime of the app, inject an `IOptions<T>` to your classes. `IOptions<T>` is a singleton, so it's loaded exactly once at startup, and you'll need to restart your app for changes to take effect. 

```csharp
// declaration
internal class AppOptions
{
    public const string ConfigurationSectionName = "App";

    public string InstanceName { get; init; } = string.Empty;
}

// registration
var section = builder.Configuration.GetSection(AppOptions.ConfigurationSectionName);
builder.Services.Configure<AppOptions>(section);

// consumption 
internal class AppInfoViewModel
{
    private readonly IOptions<AppOptions> _appOptions;

    public string InstanceName => _appOptions.Value.InstanceName;

    public AppInfoViewModel(IOptions<AppOptions> appOptions)
    {
        _appOptions = appOptions;
    }
}
```

> [!TIP]
> If you're storing an injected `IOptions<T>`, it doesn't really matter if you type your field as `IOptions<T>`, or type it as just `T` and assign `IOptions<T>.Value`. 

## Using long-lived configuration

For configuration that's tied to a scope, it's better to inject `IOptionsSnapshot<T>`. This type represents the state of the configuration when DI resolved it. 

Remember, you'll need to add `reloadOnChange: true` to any custom configuration sources, otherwise the snapshot will always represent the initial load. 

```csharp
// declaration
internal class PricingOptions
{
    public const string ConfigurationSectionName = "Pricing";

    public int GlobalDiscountPercentage { get; init; }
}

// registration
var section = builder.Configuration.GetSection(PricingOptions.ConfigurationSectionName);
builder.Services.Configure<PricingOptions>(section);

// consumption
internal class CheckoutService
{
    private readonly IOptionsSnapshot<PricingOptions> _pricingOptions;

    public CheckoutService(IOptionsSnapshot<PricingOptions> pricingOptions)
    {
        _pricingOptions = pricingOptions;
    }

    public decimal CalculateTotal()
    {
        decimal subtotal = 0;

        /* ...calculate subtotal... */

        subtotal *= 1 - (decimal)(_pricingOptions.Value.GlobalDiscountPercentage * 0.01);
        return subtotal;
    }
}
```

## Using real-time updating options

For configuration that needs to be updated in real-time, use `IOptionsMonitor<T>`. Every time you access it, it will provide an up-to-date value. 

Again, remember to add `reloadOnChange: true` when setting up configuration sources, otherwise updates won't be reflected in the options monitor. 

```csharp
// declaration
internal class LoggingOptions
{
    public const string ConfigurationSectionName = "Logging";

    public LogEventLevel LogLevel { get; init; } = LogEventLevel.Warning;
}

// registration
var section = builder.Configuration.GetSection(LoggingOptions.ConfigurationSectionName);
builder.Services.Configure<LoggingOptions>(section);

// consumption
internal class FileLogEventSink : ILogEventSink
{
    private readonly IOptionsMonitor<LoggingOptions> _loggingOptions;

    public FileLogEventSink(IOptionsMonitor<LoggingOptions> loggingOptions)
    {
        _loggingOptions = loggingOptions;
    }

    public void Emit(LogEvent logEvent)
    {
        if (logEvent.Level < _loggingOptions.CurrentValue.LogLevel)
        {
            return;
        }

        // ...
    }
}
```

The options monitor is surprisingly cheap to use. It doesn't re-load all configuration sources each time it's accessed, nor does it repeatedly poll the source; instead, each subscribes to an `IChangeToken`, which notifies it when the source has changes. 

## Using multiple named configurations of one type

If you have multiple configurations of the same type, you can iterate over a section and add multiple keyed configurations. For example, for the following configuration: 

```json
{
    "AuthProviders": {
        "Facebook": { /* ... */ },
        "Google": { /* ... */ }
    }
}
```

The registration would be: 

```csharp
IConfigurationSection section = builder.Configuration.GetSection("AuthProviders");
foreach (var provider in section)
{
    builder.Services.Configure<AuthProviderOptions>(section.Key, section);
}
```

To make keys more discoverable to consumers, you may also want to set up a registry. 

```csharp
// declaration
internal class AuthProviderOptions
{
    public string Name { get; init; } = string.Empty;
    // ...
}

internal class AuthProviderRegistry
{
    public string[] Keys { get; }

    public AuthProviderRegistry(string[] keys)
    {
        Keys = keys;
    }
}

// registration (static version)
IConfigurationSection section = builder.Configuration.GetSection("AuthProviders");
string[] keys = section.GetChildren().Select(x => x.Key).ToArray();
builder.Services.AddSingleton<AuthProviderRegistry>(_ => new(keys))

// registration (monitoring version)
builder.Services.AddTransient<AuthProviderRegistry>(sp => new(
    sp.GetRequiredService<IConfiguration>()
        .GetSection("AuthProviders")
        .GetChildren()
        .Select(x => x.Key)
        .ToArray()
));

// consumption
internal class AuthService
{
    private readonly IOptionsMonitor<AuthProviderOptions> _authProviderOptions;
    private readonly AuthProviderRegistry _authProviderRegistry;

    public AuthService(IOptionsMonitor<AuthProviderOptions> authProviderOptions,
                       AuthProviderRegistry authProviderRegistry)
    {
        _authProviderOptions = authProviderOptions;
        _authProviderRegistry = authProviderRegistry;
    }

    public IEnumerable<string> GetProviderNames() 
    {
        foreach (string key in _authProviderRegistry.Keys)
        {
            yield return _authProviderOptions.Get(key).Name;
        }
    }
}
```

>[!NOTE]
> `IOptions<T>` doesn't expose a `.Get(string)`, because it represents "the" instance of `T`. You'll have to use `IOptionsSnapshot` or `IOptionsMonitor` here. 
