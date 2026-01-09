try:
    import rgb_lib
    print("MultisigWallet methods:", [m for m in dir(rgb_lib.MultisigWallet) if m.startswith('post_')])
except Exception as e:
    print(e)
