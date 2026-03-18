interface Props {
  username: string
  onLogout: () => void
}

export function Header({ username, onLogout }: Props) {
  return (
    <header className="header">
      <h1>NaturalQuery</h1>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ color: '#4b5563', fontSize: 13 }}>{username}</span>
        <button className="btn btn-secondary" style={{ width: 'auto', padding: '5px 12px', fontSize: 12 }} onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  )
}
