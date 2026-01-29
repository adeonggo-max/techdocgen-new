namespace Contracts;

public record OrderCreated(Guid OrderId, string CustomerId, decimal Amount, DateTime CreatedAt);
