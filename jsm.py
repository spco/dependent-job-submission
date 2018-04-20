import argparse
import json
import subprocess
# Reads in a json file. Each item in the json file is a job to submit. The contents are its name, and which jobs
# it depends upon. The program takes the jobs, submits them to torque, and captures the jobIDs returned.
# These are then used as inputs for the jobs which are dependent.

y = 0


def submit_job(stage, dependency_ids):
    global y
    # increment the jobid - this is a mock part since I don't get anything back from echo but do from qsub
    y += 1
    if dependency_ids:
        command = 'echo "-W depend=afterok:' + ':'.join([str(item) for item in dependency_ids]) + '"'
    else:
        command = 'echo'
    print(command)
    # Execute command in bash
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error is not None:
        print("Abort - something went wrong in submitting!")
        print("Stage name:", stage, "dependent on", dependency_ids)
        exit(1)
    print("submitting " + str(stage) + " with job id " + str(y) + ", dependent on jobs", dependency_ids)
    return y


def attempt_to_submit_next_stage(index, stages, submitted_stages, data, jobids):
    if stages[index] in submitted_stages:
        # this stage already submitted - move on
        # print("already submitted stage " + str(index) + ": " + stages[index])
        return
    else:
        # look at the dependencies of the index-th stage. If all are in submitted_stages, this is ready for submit.
        # Otherwise, move on.
        dependencies = data[stages[index]]["depends_on"].split(",")
        # print('dependencies:', dependencies)
        if set(dependencies).issubset(set(submitted_stages)):
            if dependencies != [""]:
                dep_indices = [jobids[stages.index(item)] for item in dependencies]
            else:
                dep_indices = []
            # print("can submit stage " + str(index) + ": " + stages[index] + " with dependency job ids", dep_indices)
            # submit stage
            jobids[index] = submit_job(stages[index], dep_indices)
            submitted_stages.append(stages[index])
            return
        else:
            print("cannot yet submit stage " + str(index) + ": " + stages[index] + ", because of dependency on " +
                  ', '.join([str(item) for item in set(dependencies).difference(submitted_stages)]))
    return


def djs(args):
    json_data = open(args.input_file).read()

    data = json.loads(json_data)

    list_of_stages = [stages for stages in data]
    print("Stages to be submitted:")
    print(list_of_stages)
    jobids = ["" for _ in list_of_stages]
    list_of_submitted_stages = [""]
    index = -1
    second_index = 0
    # Loop while there are un-submitted jobs, or until we loop through len(list_of_stages)^2 times,
    # in which case we must have hit an unresolvable dependency
    while len(list_of_submitted_stages) < len(list_of_stages) + 1 and second_index < len(list_of_stages)*len(list_of_stages):
        index += 1
        index = index % len(list_of_stages)
        second_index += 1
        attempt_to_submit_next_stage(index, list_of_stages, list_of_submitted_stages, data, jobids)

    print("\nAll jobs submitted!")


def create_parser():
    parser = argparse.ArgumentParser(description='Run the IASI native (L1C and L2) to NetCDF conversion process.')
    parser.add_argument('input_file', type=str,
                        help='A string in containing the filename of the JSON file to read in from.')
    return parser


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    djs(args)
