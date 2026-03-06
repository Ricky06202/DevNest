using System.Net.Http.Json;
using System.Text.Json;
using frontend.Models;
using Microsoft.JSInterop;
using System.Net.Http.Headers;

namespace frontend.Providers
{
    public class AuthService
    {
        private readonly HttpClient _httpClient;
        private readonly IJSRuntime _jsRuntime;
        private readonly CustomAuthenticationStateProvider _authStateProvider;

        public AuthService(HttpClient httpClient, IJSRuntime jsRuntime, CustomAuthenticationStateProvider authStateProvider)
        {
            _httpClient = httpClient;
            _jsRuntime = jsRuntime;
            _authStateProvider = authStateProvider;
        }

        public async Task<bool> LoginAsync(LoginRequest request)
        {
            // FastAPI OAuth2PasswordRequestForm expects x-www-form-urlencoded
            var loginData = new FormUrlEncodedContent(new[]
            {
                new KeyValuePair<string, string>("username", request.Username),
                new KeyValuePair<string, string>("password", request.Password)
            });

            var response = await _httpClient.PostAsync("login", loginData);

            if (response.IsSuccessStatusCode)
            {
                var result = await response.Content.ReadFromJsonAsync<LoginResponse>();
                if (result != null && !string.IsNullOrEmpty(result.access_token))
                {
                    // Guardar token en local storage usando JSInterop nativo
                    await _jsRuntime.InvokeVoidAsync("localStorage.setItem", "authToken", result.access_token);
                    
                    // Actualizar el estado de autenticación
                    _authStateProvider.NotifyUserAuthentication(result.access_token);
                    
                    // Configurar el header global para futuras peticiones
                    _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", result.access_token);
                    return true;
                }
            }
            return false;
        }

        public async Task<AuthResult> RegisterAsync(RegisterRequest request)
        {
            var response = await _httpClient.PostAsJsonAsync("register", request);
            if (response.IsSuccessStatusCode)
            {
                return new AuthResult { Success = true };
            }
            
            var error = "Ocurrió un error en el registro.";
            try 
            {
                var errorData = await response.Content.ReadFromJsonAsync<JsonElement>();
                if (errorData.TryGetProperty("detail", out var detail))
                {
                    error = detail.GetString() ?? error;
                }
            } catch { /* Ignorar error de parseo */ }

            return new AuthResult { Success = false, ErrorMessage = error };
        }

        public async Task LogoutAsync()
        {
            await _jsRuntime.InvokeVoidAsync("localStorage.removeItem", "authToken");
            _authStateProvider.NotifyUserLogout();
            _httpClient.DefaultRequestHeaders.Authorization = null;
        }
    }

    public class AuthResult
    {
        public bool Success { get; set; }
        public string? ErrorMessage { get; set; }
    }
}
