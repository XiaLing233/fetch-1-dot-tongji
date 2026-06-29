// 加密逻辑

import JSEncrypt from 'jsencrypt';
import CryptoJS from 'crypto-js';

// 密码加密，使用 RSA 公钥加密
export function passwordEncrypt(password) {
    let encrypt = new JSEncrypt({ keySize: 2048 });

    const pub_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA3v4UYdRFA8+P8QT79CZhsDLsRFRa/yEFXBP/eH8u2dzOpX47ep01E/Z6A8FKfTogoeVrKqjiaWBXub4+LBllOJGmfnVx7YK73jUe7zMrEE05opgkFE/jpc0zE3K8UQKh31aLniZ961Q7NtAqwe/c/ksLmVa/UwIow23H5ELIQfR8mY/Zvq/0LeJIpABm2y3kzFLEfXx+4trPw2ceqP99qn+hgds06q6CdguyUzzot1ZrJGqX5uKevIAuTrWWBhzdrlzzXjLch3T36XdwByFW5Zg0YLK5Ka3VkyKhcFBBjJ8DFSqQrl+qe6m4EJtqrfNHCwmFjlpkwCp52ndkkQZDPwIDAQAB";
    encrypt.setPublicKey(pub_key);
    
    let encrypted = encrypt.encrypt(password);

    return encodeURIComponent(encrypted); // 返回 URI 编码的加密密码，1 系统是在提交函数中做的，这里放在加密函数中
}

// 链接加密，使用 AES 加密
export function urlEncrypt(url) {
    // AES 加密
    let iv = CryptoJS.enc.Utf8.parse("(OjRK9qSRad:W?b|");

    let preparation = {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
    }

    let urlEncoded = encodeURIComponent(url);
    let key = CryptoJS.enc.Utf8.parse("L>Kb|&:WwTQ0vQkx");
    let urlEncrypted = CryptoJS.AES.encrypt(String(urlEncoded), key, preparation);

    return encodeURIComponent(CryptoJS.enc.Base64.stringify(urlEncrypted.ciphertext));
}
