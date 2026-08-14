"use client";

import { useEffect, useRef, useState } from "react";
import type { UserProfile } from "@/lib/dashboard-data";

type UserMenuProps = {
  profile: UserProfile;
};

export function UserMenu({ profile }: UserMenuProps) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  return (
    <div ref={menuRef} className="relative">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Open profile menu"
        onClick={() => setOpen((current) => !current)}
        className="avatar-button"
      >
        <span>{profile.avatarInitials}</span>
      </button>

      {open ? (
        <div className="menu-panel" role="menu" aria-label="User menu">
          <p className="menu-name">{profile.name}</p>
          <p className="menu-meta">{profile.role}</p>
          <p className="menu-meta">{profile.email}</p>
          <button type="button" className="menu-signout" role="menuitem">
            Sign out
          </button>
          <p className="menu-footnote">MVP placeholder</p>
        </div>
      ) : null}
    </div>
  );
}
