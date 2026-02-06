export const isAdmin = (user) => {
  if (!user) return false;
  // Check for specific username 'ray40' OR role 'admin'
  return user.username === 'ray40' || user.role === 'admin';
};
