interface Props {
  username: string
  onLogout: () => void
}

export function Header({ username, onLogout }: Props) {
  return (
    <header className="header">
      <h1 className="logo-text">NaturalQuery</h1>
      <div className="header-right">
        <div className="user-badge">
          <span className="user-badge-dot" />
          {username}
        </div>
        <button
          className="btn btn-secondary"
          style={{ width: 'auto', padding: '5px 12px', fontSize: 12 }}
          onClick={onLogout}
        >
          Logout
        </button>
      </div>
    </header>
  )
}
