import React, { useState } from 'react';

const Login = ({ onLoginSuccess }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('http://localhost:5000/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                onLoginSuccess();
            } else {
                setError("Tài khoản hoặc mật khẩu sai!");
            }
        } catch (err) {
            setError("Lỗi kết nối server Auth.");
        }
    };

    return (
        <div style={styles.container}>
            <form onSubmit={handleSubmit} style={styles.form}>
                <h2 style={styles.title}>ĐĂNG NHẬP HỆ THỐNG</h2>
                {error && <p style={styles.error}>{error}</p>}
                <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} style={styles.input} />
                <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} style={styles.input} />
                <button type="submit" style={styles.button}>ĐĂNG NHẬP</button>
            </form>
        </div>
    );
};

const styles = {
    container: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#121212' },
    form: { background: '#1e1e2f', padding: '40px', borderRadius: '16px', width: '350px', border: '1px solid #00f2fe', textAlign: 'center' },
    title: { color: '#00f2fe', marginBottom: '20px' },
    input: { width: '100%', padding: '12px', marginBottom: '15px', borderRadius: '8px', border: '1px solid #333', background: '#0f0c29', color: '#fff', boxSizing: 'border-box' },
    button: { width: '100%', padding: '12px', background: 'linear-gradient(to right, #00f2fe, #4facfe)', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' },
    error: { color: '#ff4757', marginBottom: '10px' }
};

export default Login;