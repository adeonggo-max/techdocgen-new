using Microsoft.EntityFrameworkCore;

namespace OrderWorker.Data;

public class DotnetDbContext : DbContext
{
    public DotnetDbContext(DbContextOptions<DotnetDbContext> options) : base(options){}
    public DbSet<Order> Orders => Set<Order>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Order>(entity => 
        {
            entity.ToTable("order");
            entity.HasKey(e => e.OrderId);
            entity.Property(e => e.OrderId).HasColumnName("order_id");
            entity.Property(e => e.CustomerId).HasColumnName("customer_id");
            entity.Property(e => e.Amount).HasColumnName("amount");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at");
        });
    }
}