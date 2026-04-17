## Setting up the container 

First, install Microsoft.Extensions.DependencyInjection. 

Then, create a service collection. This collection will hold the definitions for services, kind of like recipes. 

```csharp 
IServiceCollection sc = new ServiceCollection();
```

There are a few things you need to consider when adding a service. 

The first is the lifetime. There are 3 lifetimes available to a service: "singleton", where everyone gets the same instance; "scoped", where dependents in a given scope share the same instance; and "transient", where a new instance is constructed every time it's asked for.

The next is the service type. This is what you'll ask for when requesting the service - it doesn't have to be the absolute concrete type. For example, a dependent could ask for an `IRepository<User>` - it might get back an `InMemoryRepository<User>` or `SqliteRepository<User>`, but the dependent doesn't really need to know or care. This is great for testing since you can easily swap out dependencies with mockup versions. 

Finally, you've got the implementation type. This is the actual concrete type that will be built. If you just specify the type, the container will attempt to construct it using the other services it has. If you depend on classes that aren't in the container, you can also give it a Func<IServiceProvider,T> to show it how to construct the type. 

Examples:

```csharp 
sc.AddSingleton<Service1>();
sc.AddScoped<IService2, Service2>();
sc.AddTransient<IService3>(sp => new Service3(sp.GetRequiredService<IService4>()));
```

## Using the provider 

You can call the extension method `.BuildServiceProvider()` on the service collection to build an `IServiceProvider`. You can then use `GetService<TService>` (which might return null) or `GetRequiredService<TService>` (which will throw if the service can't be constructed) to construct the entry point of your app. 


