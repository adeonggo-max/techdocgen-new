using MassTransit;
using Contracts;
using OrderWorker.Data;

public class CreateOrderConsumer : IConsumer<CreateOrder>
{
    private readonly DotnetDbContext _db;
    
    public CreateOrderConsumer(DotnetDbContext db)
    {
        _db = db;
    }

    public async Task Consume(ConsumeContext<CreateOrder> context)
    {
        var cmd = context.Message;

        Console.WriteLine($"[Worker] CreateOrder received: {cmd.OrderId}, customer={cmd.CustomerId}, amount={cmd.Amount}");

        var order = new Order
        {
            OrderId = cmd.OrderId,
            CustomerId = cmd.CustomerId,
            Amount = cmd.Amount,
            CreatedAt = DateTime.UtcNow
        };

        _db.Orders.Add(order);
        await _db.SaveChangesAsync();
         Console.WriteLine($"[Worker] Order saved to MySQL: {order.OrderId}");

        var evt = new OrderCreated(cmd.OrderId, cmd.CustomerId, cmd.Amount, DateTime.UtcNow);
        await context.Publish(evt);

        Console.WriteLine($"[Worker] Published OrderCreated for {cmd.OrderId}");
    }
}