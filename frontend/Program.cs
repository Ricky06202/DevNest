using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using Microsoft.AspNetCore.Components.Authorization;
using frontend;
using frontend.Providers;
using MudBlazor.Services;

var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");
builder.RootComponents.Add<HeadOutlet>("head::after");

// Set base address properly to backend API (or localhost:8000 for debug)
builder.Services.AddScoped(sp => new HttpClient { BaseAddress = new Uri("http://localhost:8000/") });

// Register Auth services
builder.Services.AddAuthorizationCore();
builder.Services.AddScoped<CustomAuthenticationStateProvider>();
builder.Services.AddScoped<AuthenticationStateProvider>(s => s.GetRequiredService<CustomAuthenticationStateProvider>());
builder.Services.AddScoped<AuthService>();

builder.Services.AddMudServices();

await builder.Build().RunAsync();
