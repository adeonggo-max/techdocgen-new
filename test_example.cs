using System;

namespace Example
{
    /// <summary>
    /// Simple example C# class for testing documentation generation
    /// </summary>
    public class Greeter
    {
        private string name;
        
        /// <summary>
        /// Initializes a new instance of the Greeter class
        /// </summary>
        /// <param name="name">The name to greet</param>
        public Greeter(string name)
        {
            this.name = name;
        }
        
        /// <summary>
        /// Gets or sets the name property
        /// </summary>
        public string Name
        {
            get { return name; }
            set { name = value; }
        }
        
        /// <summary>
        /// Greets the person by name
        /// </summary>
        /// <returns>A greeting message</returns>
        public string Greet()
        {
            return $"Hello, {name}!";
        }
        
        /// <summary>
        /// Main entry point
        /// </summary>
        public static void Main(string[] args)
        {
            var greeter = new Greeter("World");
            Console.WriteLine(greeter.Greet());
        }
    }
}







