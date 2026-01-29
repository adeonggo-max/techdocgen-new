namespace OrderWorker.Data;
public class Order
{
    public Guid OrderId {get; set;}
    public string CustomerId {get; set;}

    public decimal Amount {get; set;}

    public DateTime CreatedAt {get; set;}
}