import sys

def check_args():
    if len(sys.argv) < 3:
        print 'Correct usage is "python discriminator.py [base_file] [discrim_1] ... [discrim_n]"'
        return False

    return True

if __name__ == '__main__':
    if check_args():
        all_lines = set()

        file_iter = range(len(sys.argv))
        del file_iter[1] # Index 1 is removed before index 0 in order to remove the correct element.
        del file_iter[0]

        for i in file_iter:
            with open(sys.argv[i], 'r') as read_file:
                for line in read_file:
                    all_lines.add(line)

        # Now create base

        base_lines = set()

        with open(sys.argv[1], 'r') as base:
            for line in base:
                base_lines.add(line)
        
        # Do the discriminating...
        base_lines -= all_lines
        
        # Now write the result into the file
        with open('result.out', 'w') as discrim:
            for line in base_lines:
                discrim.write(line)
