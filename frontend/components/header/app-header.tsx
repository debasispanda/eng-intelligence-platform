import type { UserProfile } from "@/lib/dashboard-data";
import { UserMenu } from "@/components/header/user-menu";

type AppHeaderProps = {
  appTitle: string;
  profile: UserProfile;
};

export function AppHeader({ appTitle, profile }: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="app-header-inner">
        <div className="brand-block" aria-label="App brand">
          <span className="brand-logo" aria-hidden="true" />
          <span className="brand-title">{appTitle}</span>
        </div>
        <UserMenu profile={profile} />
      </div>
    </header>
  );
}
