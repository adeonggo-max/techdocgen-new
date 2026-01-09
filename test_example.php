<?php

/**
 * Simple example PHP class for testing documentation generation
 */
class UserManager
{
    private $users = [];
    
    /**
     * Constructor
     */
    public function __construct()
    {
        $this->users = [];
    }
    
    /**
     * Add a user to the collection
     * @param string $name User name
     * @param string $email User email
     * @return bool True if successful
     */
    public function addUser($name, $email)
    {
        $this->users[] = [
            'name' => $name,
            'email' => $email
        ];
        return true;
    }
    
    /**
     * Get all users
     * @return array List of users
     */
    public function getUsers()
    {
        return $this->users;
    }
    
    /**
     * Find user by email
     * @param string $email Email to search for
     * @return array|null User data or null if not found
     */
    public function findUserByEmail($email)
    {
        foreach ($this->users as $user) {
            if ($user['email'] === $email) {
                return $user;
            }
        }
        return null;
    }
}







