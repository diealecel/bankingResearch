import sys

def check_args():
    if len(sys.argv) < 3:
        print 'Correct usage is "python merger.py [file_1] [file_2] ... [file_n]"'
        return False

    return True

if __name__ == '__main__':
    if check_args():
        all_lines = set()

        file_iter = range(len(sys.argv))
        del file_iter[0]

        for i in file_iter:
            with open(sys.argv[i], 'r') as read_file:
                for line in read_file:
                    all_lines.add(line)

        with open('merged.out', 'w') as merged:
            for line in all_lines:
                merged.write(line)
