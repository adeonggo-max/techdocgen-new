namespace Contracts;

public record CreateOrder(Guid OrderId, string CustomerId, decimal Amount);