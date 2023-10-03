# -------------------------------------------------------------------------------
# Author: Ruggero Citton
# Date: September 18 , 2023
# Purpose: Send a notification in case of public IP change
# Tested on: Ubuntu 23.04 - Raspberry PI 4
#
#
# Licensed under The MIT License (MIT).
# See included LICENSE file or the notice below.
#
# Copyright (c) 2023 Ruggero Cittons
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -------------------------------------------------------------------------------



###########################
CONTAINER=ipchange_check
IMGNME=ip-change_check
IMGVRS=1.0.0
DOCKER=/usr/bin/docker
PODMAN=/usr/bin/podman
RUNTIMECT=$(DOCKER)


###############################################################################
#                             DOCKER/PODMAN SECTION                           #
###############################################################################

all: build \
	create \
	start \
	setup

build:
	@echo "Make CONTAINER $(CONTAINER)"
	$(RUNTIMECT) build --force-rm=true \
	--no-cache=true -t $(IMGNME):$(IMGVRS) -f Dockerfile .

create:
	@echo "Create CONTAINER $(CONTAINER)"
    ifeq ($(RUNTIMECT),/usr/bin/docker)
		$(RUNTIMECT) create -t -i \
			--hostname $(CONTAINER) \
			--label com.centurylinklabs.watchtower.enable="false" \
			--volume /etc/localtime:/etc/localtime:ro \
			--restart=always \
			--name $(CONTAINER) \
			$(IMGNME):$(IMGVRS)
    else
		$(RUNTIMECT) create -t -i \
			--hostname $(CONTAINER) \
			--label com.centurylinklabs.watchtower.enable="false" \
			--volume /etc/localtime:/etc/localtime:ro \
			--restart=always \
			--name $(CONTAINER) \
			$(IMGNME):$(IMGVRS)
    endif

start:
	@echo "STARTING UP CONTAINER $(CONTAINER)"
	$(RUNTIMECT) start $(CONTAINER)

stop:
	@echo "STOPPING CONTAINER $(CONTAINER)"
	$(RUNTIMECT) stop $(CONTAINER)

clean:
	@echo "Cleanup CONTAINER $(CONTAINER)"
	-$(RUNTIMECT) stop $(CONTAINER)
	-$(RUNTIMECT) rm $(CONTAINER)
	$(RUNTIMECT) rmi $(IMGNME):$(IMGVRS)

connect:
	$(RUNTIMECT) exec -it $(CONTAINER) bash

test:
	$(RUNTIMECT) exec -it $(CONTAINER) python3 /app/notification_test.py

setup:
	$(RUNTIMECT) exec -it $(CONTAINER) python3 /app/initial_config.py
###############################################################################
#                                                                             #
###############################################################################
