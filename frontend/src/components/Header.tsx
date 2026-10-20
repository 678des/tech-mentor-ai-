export function Header() {
  return (
    <header className="flex">
      <div>
        <h1>IT News for Student</h1>
      </div>
      <div className="m-4">
        <button className="m-4">LatestNews</button>
        <button className="m-4">MyPage</button>
        <button className="bg-red-300">news取得</button>
      </div>
    </header>
  );
}
