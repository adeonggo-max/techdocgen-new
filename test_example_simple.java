package com.example;

/**
 * Simple Hello World class for testing
 */
public class HelloWorld {
    
    private String message;
    
    public HelloWorld(String message) {
        this.message = message;
    }
    
    public void printMessage() {
        System.out.println(message);
    }
    
    public String getMessage() {
        return message;
    }
    
    public static void main(String[] args) {
        HelloWorld hello = new HelloWorld("Hello, World!");
        hello.printMessage();
    }
}







