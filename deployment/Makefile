.PHONY: build clean
.PHONY: vpc-stack
.PHONY: leader-stack follower-stack
.PHONY: leader-ami follower-ami

build:
	@find troposphere -name "*.py" | grep -v "utils" | xargs -I{} python {}

clean:
	@rm troposphere/*.json

vpc-stack:
	./deployment-helper.sh create-vpc-stack

leader-stack:
	./deployment-helper.sh create-leader-stack

follower-stack:
	./deployment-helper.sh create-follower-stack

leader-ami:
	./deployment-helper.sh create-leader-ami

follower-ami:
	./deployment-helper.sh create-follower-ami
