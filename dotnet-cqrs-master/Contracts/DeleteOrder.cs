namespace Contracts;

public record DeleteOrder(Guid OrderId, string CustomerId, decimal Amount, string RemovedBy);