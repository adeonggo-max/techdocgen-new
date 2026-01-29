using Contracts;
using Hangfire;
using MassTransit;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace OrderApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [Authorize]
    public class OrderController : ControllerBase
    {
        private readonly ISendEndpointProvider _sendEndpointProvider;
        private readonly IPublishEndpoint _publishEndpoint;

        private readonly IBackgroundJobClient _jobs;

        public OrderController(ISendEndpointProvider sendEndpointProvider, IPublishEndpoint publishEndpoint, IBackgroundJobClient jobs)
        {
            _sendEndpointProvider = sendEndpointProvider;
            _publishEndpoint = publishEndpoint;
            _jobs = jobs;
        }


        [HttpPost("create")]
        public async Task<IActionResult> CreateOrder([FromBody] CreateOrderDto dto)
        {
            var orderId = Guid.NewGuid();
            var command = new CreateOrder(orderId, dto.CustomerId, dto.Amount);

            // Send Mechanisme (must provided queue/topic name)
            // var endpoint = await _sendEndpointProvider.GetSendEndpoint(new Uri("queue:order-service-queue"));
            // await endpoint.Send(command);

            // Publish Mechanisme (Detect Object serialized to pick Consumer automatically isntead of send to topic name)
            await _publishEndpoint.Publish(command);

            // Console.WriteLine($"[API] Sent CreateOrder {orderId}");

            Console.WriteLine($"[API] PUBLISH CreateOrder {orderId}");


            // Hangfire Send Email
            _jobs.Schedule(() => Console.WriteLine("Hangfire send email "), TimeSpan.FromMinutes(1));

            return Accepted($"/api/order/create/{orderId}", new { OrderId = orderId });

        }

        [HttpPost("delete")]
        public async Task<IActionResult> deleteOrder([FromBody] DeleteOrderDto dto)
        {
            var orderId = Guid.NewGuid();
            var command = new DeleteOrder(orderId, dto.CustomerId, dto.Amount, dto.RemovedBy);

            // Send Mechanisme (must provided queue/topic name)
            // var endpoint = await _sendEndpointProvider.GetSendEndpoint(new Uri("queue:order-service-queue"));
            // await endpoint.Send(command);

            // Publish Mechanisme (Detect Object serialized to pick Consumer automatically isntead of send to topic name)
            await _publishEndpoint.Publish(command);

            // Console.WriteLine($"[API] Sent CreateOrder {orderId}");

            Console.WriteLine($"[API] PUBLISH DeleteOrder {orderId}");

            return Accepted($"/api/order/delete/{orderId}", new { OrderId = orderId, RemovedBy = dto.RemovedBy });

        }
    }

    public record CreateOrderDto(string CustomerId, decimal Amount);
    public record DeleteOrderDto(string CustomerId, decimal Amount, string RemovedBy);
}