# Admin Guide

## Robot Live Console - Administrator Features

This guide covers all administrative features and best practices for managing your Robot Live Console instance.

## Admin Features

### 1. User Management

#### View All Users
- Navigate to Admin Dashboard → Users
- See list of all registered users
- View user details: email, role, registration date, last login, activity

#### Delete User
```
DELETE /admin/users/{user_id}
```
- Removes user from database
- Deletes all bookings and sessions
- Removes workspace files and containers
- Cannot delete your own account

**Warning:** This action is permanent and cannot be undone!

#### Promote User to Admin
```
PATCH /admin/users/{user_id}/role
Body: {"role": "admin"}
```
- Grants admin privileges to user
- Admin users can access all admin features
- Cannot demote your own account

#### Activity Tracking
- Last login time
- Total login count
- Last activity timestamp
- Account creation date

### 2. Password Management

#### Change Admin Password
```
POST /admin/change-password
Body: {
  "current_password": "...",
  "new_password": "...",
  "confirm_password": "..."
}
```

Requirements:
- Current password must be correct
- New password minimum 8 characters
- New password must be different from current
- Passwords must match

### 3. Dashboard Statistics

View real-time statistics:
- Total users
- Total bookings
- Active bookings
- Unread messages
- System health

## Best Practices

### Security
1. Use strong passwords (12+ characters, mixed case, numbers, symbols)
2. Change password regularly (every 90 days)
3. Review user activity monthly
4. Remove inactive users after 6 months
5. Monitor for suspicious activity
6. Keep admin accounts to minimum necessary

### User Management
1. Only promote trusted users to admin
2. Review new user registrations
3. Respond to user messages promptly
4. Backup database before bulk operations
5. Document admin actions in external log

### Maintenance
1. Regular database backups
2. Monitor system logs
3. Keep software updated
4. Test features after updates
5. Have rollback plan

## Troubleshooting

### Cannot Delete User
- Check if you're trying to delete yourself
- Verify admin permissions
- Check database connection
- Review logs for errors

### Password Change Fails
- Verify current password is correct
- Ensure new password meets requirements
- Check for special characters in password
- Try logging out and back in

### Users Can't Login
- Check email confirmation status
- Verify database connection
- Review rate limiting logs
- Check JWT_SECRET_KEY configuration

## API Reference

All admin endpoints require admin JWT token in Authorization header:
```
Authorization: Bearer {your_jwt_token}
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/users` | List all users |
| DELETE | `/admin/users/{id}` | Delete user |
| PATCH | `/admin/users/{id}/role` | Update user role |
| POST | `/admin/change-password` | Change admin password |
| GET | `/admin/stats` | Get dashboard statistics |

## Support

Need help? Create an issue: https://github.com/shanooo773/Robot-live-console-v2/issues
