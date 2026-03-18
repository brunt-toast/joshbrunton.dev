---
title: MSAL with .NET MAUI on Android 
date: 2026-02-26
tags: [.NET, MAUI, Android, MSAL]
---

Configuring MSAL in a .NET MAUI app for Android has some ill-documented and largely unknown hurdles. This post documents the start-to-finish process of getting a user to log in and retrieving a bearer token.  

## Package References 

You'll need the package `Microsoft.Identity.Client`. This is safe to include for all platforms, so there's no need to add a condition for the Android runtime. 

```xml
<PackageReference Include="Microsoft.Identity.Client" Version="4.72.1" />
```

## Registering the browser tab activity 

A custom Activity is required to enable the browser to redirect back to your app on Android. Under the folder `/Platforms/Android`, declare the below class. 

Note that the GUID in the DataScheme must be the Client ID of the Azure application. Unfortunately, it's not possible to specify this dynamically at run time, since the value is loaded into the AndroidManifest.xml file at compile time. 

```csharp
using Android.App;
using Android.Content;
using Android.Content.PM;
using Microsoft.Identity.Client;

namespace Doings.Native.Platforms.Android;

[Activity(NoHistory = true, LaunchMode = LaunchMode.SingleTask, Exported = true)]
[IntentFilter(
    new[] { Intent.ActionView },
    Categories = new[]
    {
        Intent.CategoryDefault,
        Intent.CategoryBrowsable
    },
    DataScheme = "msal00000000-0000-0000-0000-000000000000",
    DataHost = "auth")]
public class RedirectActivity : BrowserTabActivity;
```

## Forwarding the token through the main activity 

Once the browser has redirected back to the app, the app needs some extra help to get the token back to the method that requested it. Without this extra help, authentication Tasks will never complete. 

You should have a class called `MainActivity` in the folder `/Platforms/Android`. Inside it, add the following override method. 

```csharp
using Android.Content;
using Microsoft.Identity.Client;

protected override void OnActivityResult(int requestCode, Result resultCode, Intent? data)
{
    base.OnActivityResult(requestCode, resultCode, data);
    AuthenticationContinuationHelper.SetAuthenticationContinuationEventArgs(requestCode, resultCode, data);
}
```

## Building the Public Client Application

No matter what platform you're building for, you'll need to let your public client application builder know about your Client ID, Azure instance, Tenant ID, and redirect URI. For desktop and mobile applications, the redirect URI is usually `$"msal{_clientId}://auth"`. 

On top of that, on Android, you'll need to let the public client application builder know how to get the Activity or Window to redirect to. 

You can pass in your choice of `Microsoft.Maui.ApplicationModel.Platform.CurrentActivity`, or `Microsoft.Maui.Controls.Application.Current?.Windows.FirstOrDefault()`. According to their types, both of these might be null, so it's important to handle that edge case. 

You pass them in using `WithParentActivityOrWindow`, which is an instance method on the class `PublicClientApplicationBuilder`. 

The below snippet shows a fully configured public client application builder. All methods are compatible with all platforms, so there's no need for conditional compilation.

```csharp
string clientId = "00000000-0000-0000-0000-000000000000";
string tenantId = "00000000-0000-0000-0000-000000000000";

var pcab = PublicClientApplicationBuilder.Create(clientId)
        .WithAuthority(AzureCloudInstance.AzurePublic, tenantId)
        .WithRedirectUri($"msal{clientId}://auth") 
        .WithParentActivityOrWindow(() => Platform.CurrentActivity);
```

## Acquiring and using a token 

Once the `PublicClientApplicationBuilder` is ready, is then used to build an `IPublicClientApplication`. This instance is what's ultimately used to retrieve a bearer token. 

```csharp
IPublicClientApplication pca = pcab.Build();
AuthenticationResult? authResult = await pca.AcquireTokenInteractive([ /* scopes */ ]); 
string? token = authResult?.AccessToken;
```

You can then add this token to requests to relevant resources. 

```csharp
HttpRequestMessage request = new(/* ... */);
request.Headers.Add("Authorization", $"Bearer {token}");
```

## Further Reading 

[Introduction to Activities](https://developer.android.com/guide/components/activities/intro-activities)

