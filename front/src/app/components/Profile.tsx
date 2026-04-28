import type { ProfileView } from '../api/mappers';
import type { User } from '../api/types';

interface ProfileProps {
  user: User | null;
  profile: ProfileView | null;
  loading: boolean;
  error: string;
}

export function Profile({ user, profile, loading, error }: ProfileProps) {
  if (loading) {
    return <div className="p-8">Profil yuklanmoqda...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-500">{error}</div>;
  }

  if (!user || !profile) {
    return <div className="p-8 text-muted-foreground">Profil topilmadi.</div>;
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="mb-2">Profil</h1>
        <p className="text-muted-foreground">Backenddan olingan akkaunt ma'lumotlari</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-border p-5 space-y-2">
          <h3>Akkaunt</h3>
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>Tasdiqlangan:</strong> {user.is_verified ? 'Ha' : 'Yo\'q'}</p>
          <p><strong>Yo'nalish:</strong> {profile.direction || '-'}</p>
          <p><strong>Ingliz darajasi:</strong> {profile.englishLevel || '-'}</p>
        </div>

        <div className="rounded-xl border border-border p-5 space-y-2">
          <h3>Joriy maqsad</h3>
          <p className="text-muted-foreground">{profile.currentGoal || 'Maqsad hali kiritilmagan'}</p>
          <p><strong>Boshlang'ich sozlash:</strong> {profile.isOnboarded ? 'Yakunlangan' : 'Yakunlanmagan'}</p>
        </div>
      </div>
    </div>
  );
}
