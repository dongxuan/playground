# playground

# 尝试解决ssl的问题

```
export GITHUB_ACTIONS_RUNNER_TLS_NO_VERIFY=1
export DOTNET_SYSTEM_NET_HTTP_USESOCKETSHTTPHANDLER=0
```

# 这个似乎也可以，更新下ca证书

I am on Ubuntu 16.04. This solved it for me: 

$ sudo update-ca-certificates
Updating certificates in /etc/ssl/certs...
...
done.
Use the certs folder in front of .configure in env SSL_CERT_DIR=

$ SSL_CERT_DIR=/etc/ssl/certs ./config.sh --url https://github.com/...
