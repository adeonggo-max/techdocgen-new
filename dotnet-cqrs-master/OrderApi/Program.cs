using MassTransit;
using Contracts;
using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using Hangfire;
using Hangfire.MySql;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddHangfire(
    config => config
        .UseStorage(
            new MySqlStorage
            (
                builder.Configuration.GetConnectionString("DefaultConnection"), 
                new MySqlStorageOptions
                { TablesPrefix = "hangfire" }
            )
        )
);

builder.Services.AddHangfireServer();


builder.Services.AddMassTransit(x => 
{
    x.UsingRabbitMq((ctx, cfg) => 
    {
        cfg.Host("10.254.214.145", "/", h => 
        {
            h.Username("efaktur");
            h.Password("efaktur");
        });
    });
});

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(

    // Button JWT Authorization
    c => 
    {
        c.SwaggerDoc("v1", new OpenApiInfo { Title = "Order API", Version = "v1"});
        c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
        {
            Name = "Authorization",
            Type = SecuritySchemeType.ApiKey,
            Scheme = "Bearer",
            BearerFormat = "JWT",
            In = ParameterLocation.Header,
            Description = "Masukkan JWT Token. Contoh: Bearer {ey...}"
        });
        c.AddSecurityRequirement(new OpenApiSecurityRequirement
        {
            {
                new OpenApiSecurityScheme
                {
                    Reference = new OpenApiReference
                    {
                        Type = ReferenceType.SecurityScheme,
                        Id = "Bearer"
                    }
                },
                new string[] {}
            }
        });
    }
);

var jwtSettings = builder.Configuration.GetSection("jwt");
var key = Encoding.UTF8.GetBytes(jwtSettings["key"]);

builder.Services.AddAuthentication( options => 
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer( options => 
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidateAudience = true,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,
        ValidIssuer = jwtSettings["Issuer"],
        ValidAudience = jwtSettings["Audience"],
        IssuerSigningKey = new SymmetricSecurityKey(key)

    };
});

builder.Services.AddAuthorization();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.MapControllers();

app.UseAuthentication();
app.UseAuthorization();

app.Run();
