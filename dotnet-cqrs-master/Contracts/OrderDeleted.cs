namespace Contracts;

public record OrderDeleted(Guid OrderId, string CustomerId, decimal Amount, string RemovedBy, DateTime CreatedAt);