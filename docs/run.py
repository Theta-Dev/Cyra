import sphinx.cmd.build

if __name__ == '__main__':
    sphinx.cmd.build.main(['-M', 'html', '.', '_build', '-a', '-E'])
