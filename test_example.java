package com.example.demo;

import java.util.List;
import java.util.ArrayList;

/**
 * Calculator class that provides basic arithmetic operations
 * This is a simple example class for testing documentation generation
 */
public class Calculator {
    
    private double result;
    
    /**
     * Default constructor initializes result to 0
     */
    public Calculator() {
        this.result = 0.0;
    }
    
    /**
     * Adds two numbers and returns the sum
     * @param a first number
     * @param b second number
     * @return sum of a and b
     */
    public double add(double a, double b) {
        return a + b;
    }
    
    /**
     * Subtracts second number from first number
     * @param a first number
     * @param b second number
     * @return difference of a and b
     */
    public double subtract(double a, double b) {
        return a - b;
    }
    
    /**
     * Multiplies two numbers
     * @param a first number
     * @param b second number
     * @return product of a and b
     */
    public double multiply(double a, double b) {
        return a * b;
    }
    
    /**
     * Divides first number by second number
     * @param a dividend
     * @param b divisor
     * @return quotient of a and b
     * @throws ArithmeticException if b is zero
     */
    public double divide(double a, double b) {
        if (b == 0) {
            throw new ArithmeticException("Cannot divide by zero");
        }
        return a / b;
    }
    
    /**
     * Adds a number to the internal result
     * @param value number to add
     */
    public void addToResult(double value) {
        this.result += value;
    }
    
    /**
     * Gets the current result value
     * @return current result
     */
    public double getResult() {
        return this.result;
    }
    
    /**
     * Resets the result to zero
     */
    public void reset() {
        this.result = 0.0;
    }
    
    /**
     * Calculates the power of a number
     * @param base the base number
     * @param exponent the exponent
     * @return base raised to the power of exponent
     */
    public double power(double base, double exponent) {
        return Math.pow(base, exponent);
    }
}







