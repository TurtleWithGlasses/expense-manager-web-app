# Avatar Storage Fix - Database-Based Solution

## Problem
Profile pictures were being lost after each deployment because they were stored in the filesystem (`static/uploads/avatars/`), which is ephemeral on cloud platforms like Railway.

## Solution
Changed avatar storage from filesystem to database by storing images as base64-encoded data URIs directly in the `avatar_url` column.

## Changes Made

### 1. User Model (`app/models/user.py`)
- **Changed**: `avatar_url` column type from `String(500)` to `Text`
- **Reason**: Base64-encoded 128x128 JPEG images are approximately 6,500 characters, requiring a larger field

```python
# Before
avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

# After
avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
```

### 2. Profile API (`app/api/v1/profile.py`)

#### Upload Avatar Endpoint
- **Removed**: File system storage logic
- **Added**: Base64 encoding and data URI generation
- **Changed**: Image size from 256x256 to 128x128 (smaller for database storage)
- **Changed**: JPEG quality from 90 to 85 (optimized for size)

```python
# Convert image to base64 data URI
buffered = io.BytesIO()
square_image.save(buffered, format="JPEG", quality=85, optimize=True)
img_bytes = buffered.getvalue()
img_base64 = base64.b64encode(img_bytes).decode('utf-8')
data_uri = f"data:image/jpeg;base64,{img_base64}"

# Store in database
user.avatar_url = data_uri
```

#### Delete Avatar Endpoint
- **Removed**: File deletion logic (no longer needed)
- **Simplified**: Only clears the database field

#### Delete Account Endpoint
- **Removed**: Avatar file cleanup logic

## Benefits

1. **Persistence**: Avatars survive deployments and container restarts
2. **Simplicity**: No need to manage file uploads, storage, or cleanup
3. **Portability**: Works consistently across all deployment environments
4. **Backup**: Avatars are included in database backups automatically

## Technical Details

### Image Specifications
- **Format**: JPEG (optimized for web)
- **Size**: 128x128 pixels (square)
- **Quality**: 85% (good balance between quality and file size)
- **Encoding**: Base64 with data URI prefix
- **Approximate size**: 5-7 KB per avatar

### Data URI Format
```
data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA...
```

### Database Storage
- **Column**: `users.avatar_url` (TEXT type)
- **Max size**: Practically unlimited (TEXT type in SQLite)
- **Typical size**: 6,000-7,000 characters per avatar

## Migration Notes

### For Existing Deployments
If you have existing users with filesystem-based avatars:

1. Users will need to re-upload their avatars
2. Old avatar files in `static/uploads/avatars/` can be safely deleted
3. The database column type change will be applied automatically by SQLAlchemy

### For New Deployments
No migration needed - the new schema will be created automatically.

## Performance Considerations

### Pros
- No additional HTTP requests for avatar images
- Faster page loads (embedded in HTML)
- No filesystem I/O overhead

### Cons
- Slightly larger database size
- Larger HTML payload when avatars are displayed
- Not cacheable by browser (embedded in page)

### Optimization
The 128x128 size and 85% quality are chosen to balance quality with database size. Typical avatar sizes are 5-7 KB, which is acceptable for database storage.

## Browser Compatibility
Data URIs are supported by all modern browsers:
- Chrome: ✓
- Firefox: ✓
- Safari: ✓
- Edge: ✓
- Mobile browsers: ✓

## Security Considerations

### Input Validation
- File type validation (JPEG, PNG, GIF, WEBP only)
- File size limit: 5 MB maximum
- Image format verification using PIL
- Automatic conversion to JPEG (removes EXIF data)

### Storage Security
- Images stored as data URIs in database
- No direct file system access required
- Automatic SQL injection protection via SQLAlchemy ORM

## Testing

To test the fix:

1. **Upload a new avatar**:
   - Go to Settings → Profile
   - Upload an image
   - Verify it displays correctly

2. **Check persistence**:
   - Restart the application
   - Log in and verify avatar is still visible

3. **Deploy test** (Railway):
   - Redeploy the application
   - Log in and verify avatar persists

## Rollback Plan

If issues occur, revert these files:
- `app/models/user.py` (change Text back to String(500))
- `app/api/v1/profile.py` (restore filesystem storage logic)

## Future Enhancements

Possible improvements for the future:

1. **Lazy loading**: Load avatars asynchronously to reduce initial page load
2. **CDN storage**: Move to S3/CloudFlare R2 for better performance
3. **Multiple sizes**: Store different resolutions for different contexts
4. **WebP format**: Use WebP for better compression (requires browser support check)
5. **Caching**: Implement client-side caching strategy for base64 avatars

## Conclusion

This change ensures profile pictures persist across deployments while maintaining simplicity and portability. The database-based approach is ideal for applications deployed on ephemeral filesystems like Railway, Heroku, or Docker containers.
