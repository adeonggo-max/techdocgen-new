using MassTransit;
using Contracts;

public class DeleteOrderConsumer : IConsumer<DeleteOrder>
{
    public async Task Consume(ConsumeContext<DeleteOrder> context)
    {
        var cmd = context.Message;

        Console.WriteLine($"[Worker] DeleteOrder received: {cmd.OrderId}, customer={cmd.CustomerId}, amount={cmd.Amount}, removedBy={cmd.RemovedBy}");

        await Task.Delay(200);

        var evt = new OrderDeleted(cmd.OrderId, cmd.CustomerId, cmd.Amount, cmd.RemovedBy, DateTime.UtcNow);
        await context.Publish(evt);

        Console.WriteLine($"[Worker] Published OrderDeleted for {cmd.OrderId}");
    }

}