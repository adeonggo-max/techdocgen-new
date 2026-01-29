using MassTransit;
using Contracts;
using OrderWorker.Data;
using Microsoft.EntityFrameworkCore;

var host = Host.CreateDefaultBuilder(args)
    .ConfigureServices((context, services) =>
    {

        var connectionString = "server=localhost;port=3306;database=dotnetdb;user=root;password=";

        services.AddDbContext<DotnetDbContext>(options => options.UseMySql(connectionString, ServerVersion.AutoDetect(connectionString)));

        services.AddMassTransit(x => {
            x.AddConsumer<CreateOrderConsumer>();
            x.AddConsumer<DeleteOrderConsumer>();
            x.UsingRabbitMq((ctx, cfg) => 
            {
                cfg.Host("10.254.214.145", "/", h=>
                {
                    h.Username("efaktur");
                    h.Password("efaktur");
                });

                cfg.ConfigureEndpoints(ctx);
            });
        });
    }).Build();
    
await host.RunAsync();
