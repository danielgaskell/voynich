# Copyright (c) 2022, Daniel E. Gaskell and Claire L. Bowern.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software, datasets, and associated documentation files (the "Software
# and Datasets"), to deal in the Software and Datasets without restriction,
# including without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software and Datasets, and to
# permit persons to whom the Software is furnished to do so, subject to the
# following conditions:
# 
# - The above copyright notice and this permission notice shall be included
#   in all copies or substantial portions of the Software and Datasets.
# - Any publications making use of the Software and Datasets, or any substantial
#   portions thereof, shall cite the Software and Datasets's original publication:
# 
# > Gaskell, Daniel E., Claire L. Bowern, 2022. Gibberish after all? Voynichese
#   is statistically similar to human-produced samples of meaningless text. CEUR
#   Workshop Proceedings, International Conference on the Voynich Manuscript 2022,
#   University of Malta.
#   
# THE SOFTWARE AND DATASETS ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
# EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE AND DATASETS.

library(dplyr)
library(tibble)
library(ggplot2)
library(ggrepel)
library(ggridges)
library(randomForest)
library(MKinfer)

save_files <- T
unknowledgeable_only <- F

# ========================================================================
# Load metrics
# ========================================================================

metrics <- read.csv("metrics_paperv1.csv", header=T, stringsAsFactors=F)
vars <- colnames(metrics)
vars <- vars[2:length(vars)]
metrics <- metrics %>%
    left_join(read.csv("metadata.csv", header=T, stringsAsFactors=F))
if (unknowledgeable_only)
    metrics <- metrics %>% filter(!(group %in% c("Experimenter")))#filter(!(group %in% c("Experimenter", "2019 class")))

metrics$type <- "Technical"
metrics[which(regexpr(" - Literary - ", metrics$text, fixed=T) != -1), "type"] <- "Literary"
for (i in 1:nrow(metrics)) {
    words = strsplit(metrics[i, "text"], " - ")[[1]]
    metrics[i, "label"] = words[2]
}
metrics$class <- gsub(" .*$", "", metrics$text)
metrics$fullclass <- paste(metrics$class, "-", metrics$type)
metrics$class <- gsub("Historical", "Natural", metrics$class)
metrics$class <- gsub("Modern", "Natural", metrics$class)
metrics$binaryclass <- 1
metrics[which(metrics$class == "Gibberish"),"binaryclass"] <- 0
metrics[which(metrics$class == "Voynichese"),"binaryclass"] <- 0

# ========================================================================
# Individual variable statistics
# ========================================================================

# function to do ridge plots
ridges_plot <- function(data, axis, mainlabel, xlabel) {
    ggplot(data, aes(x=axis, y=fullclass, fill=fullclass, label=label)) +
        labs(x=xlabel, y="") +
        ggtitle(mainlabel) +
        guides(fill=FALSE) +
        geom_density_ridges2(scale=0.75, size=0.25) +
        geom_point(cex=2, color="gray20") +
        #geom_jitter(width=0, height=0.1, cex=2, color="black", alpha=0.5) +
        geom_text_repel(size=3, color="gray20") +
        scale_x_continuous(expand=c(0,0)) +
        scale_y_discrete(expand=expansion(add=c(0,1))) +
        coord_cartesian(clip="off") +
        theme_bw() +
        theme(panel.grid = element_blank())
}

# initialize variables
norm_ranges <- tibble(var = character(), median = numeric(), x1 = numeric(), x2 = numeric(), x3 = numeric(), voyx1 = numeric(), voyx2 = numeric(), voyx3 = numeric(), english = numeric(), overlap1 = numeric(), overlap1_class = character(), overlap2 = numeric(), overlap2_class = character(), overlap3 = numeric(), overlap3_class = character(), overlap4 = numeric(), overlap4_class = character())
overlap <- tibble(var = vars, overlap1 = numeric(length(vars)), overlap2 = numeric(length(vars)), overlap3 = numeric(length(vars)), overlap4 = numeric(length(vars)))
ttests <- tibble(var = vars, G_M = numeric(length(vars)), G_V = numeric(length(vars)), V_M = numeric(length(vars)), S_N = numeric(length(vars)), G_E = numeric(length(vars)), class_years = numeric(length(vars)))
ttests_dir <- tibble(var = vars, G_M = numeric(length(vars)), G_V = numeric(length(vars)), V_M = numeric(length(vars)), S_N = numeric(length(vars)), G_E = numeric(length(vars)), class_years = numeric(length(vars)))

# main loop
comparison_class <- "Gibberish"
meaningful <- metrics %>% filter(class %in% c("Natural", "Conlangs"))
gibberish <- metrics %>% filter(class == "Gibberish" )
voynichese <- metrics %>% filter(class == "Voynichese")
for (var in vars) {
    # plot density ridges
    print(var)
    print(ridges_plot(metrics, metrics[,var], var, var))
    if (save_files)
        ggsave(paste('var_', var, '.svg', sep=""), width=8, height=4)
    
    # calculate bootstrap differences
    ttests[which(ttests$var == var), "G_M"] <- boot.t.test(response ~ binaryclass, data = metrics %>% filter(class %in% c("Natural", "Conlangs", "Gibberish")) %>% rename(response = var))$p.value
    ttests[which(ttests$var == var), "G_V"] <- boot.t.test(response ~ class, data = metrics %>% filter(class %in% c("Voynichese", "Gibberish")) %>% rename(response = var))$p.value
    ttests[which(ttests$var == var), "V_M"] <- boot.t.test(response ~ binaryclass, data = metrics %>% filter(class %in% c("Voynichese", "Natural", "Conlangs")) %>% rename(response = var))$p.value
    ttests[which(ttests$var == var), "G_E"] <- boot.t.test(response ~ class, data = metrics %>% filter(class %in% c("Gibberish") | label == "English") %>% rename(response = var))$p.value
    if (!unknowledgeable_only) {
        ttests[which(ttests$var == var), "S_N"] <- boot.t.test(response ~ specialist, data = metrics %>% filter(class == "Gibberish") %>% rename(response = var))$p.value
        ttests[which(ttests$var == var), "class_years"] <- boot.t.test(response ~ group, data = metrics %>% filter(class == "Gibberish", group %in% c("2018 class", "2019 class")) %>% rename(response = var))$p.value
    }
    
    # calculate differences in group means as % of comparison group
    ttests_dir[which(ttests$var == var), "G_M"] <- (mean((metrics %>% filter(class %in% c("Gibberish")))[,var], na.rm=T) - mean((metrics %>% filter(class %in% c("Natural", "Conlangs")))[,var], na.rm=T)) / mean((metrics %>% filter(class %in% c("Natural", "Conlangs")))[,var], na.rm=T)
    ttests_dir[which(ttests$var == var), "G_V"] <- (mean((metrics %>% filter(class %in% c("Gibberish")))[,var], na.rm=T) - mean((metrics %>% filter(class %in% c("Voynichese")))[,var], na.rm=T)) / mean((metrics %>% filter(class %in% c("Voynichese")))[,var], na.rm=T)
    ttests_dir[which(ttests$var == var), "V_M"] <- (mean((metrics %>% filter(class %in% c("Voynichese")))[,var], na.rm=T) - mean((metrics %>% filter(class %in% c("Natural", "Conlangs")))[,var], na.rm=T)) / mean((metrics %>% filter(class %in% c("Natural", "Conlangs")))[,var], na.rm=T)
    ttests_dir[which(ttests$var == var), "G_E"] <- (mean((metrics %>% filter(class %in% c("Gibberish")))[,var], na.rm=T) - mean((metrics %>% filter(label == "English"))[,var], na.rm=T)) / mean((metrics %>% filter(label == "English"))[,var], na.rm=T)
    if (!unknowledgeable_only) {
        ttests_dir[which(ttests$var == var), "S_N"] <- (mean((metrics %>% filter(specialist == 1))[,var], na.rm=T) - mean((metrics %>% filter(specialist == 0))[,var], na.rm=T)) / mean((metrics %>% filter(specialist == 0))[,var], na.rm=T)
        ttests_dir[which(ttests$var == var), "class_years"] <- (mean((metrics %>% filter(group == "2019 class"))[,var], na.rm=T) - mean((metrics %>% filter(group == "2018 class"))[,var], na.rm=T)) / mean((metrics %>% filter(group == "2018 class"))[,var], na.rm=T)
    }
    
    # calculate overlap
    lower_limit   <- min(metrics[,var]) - ((max(metrics[,var]) - min(metrics[,var])) / 2)
    upper_limit   <- max(metrics[,var]) + ((max(metrics[,var]) - min(metrics[,var])) / 2)
    df_meaningful <- density(meaningful[,var], from=lower_limit, to=upper_limit, n=1024)
    df_gibberish  <- density(gibberish[,var], from=lower_limit, to=upper_limit, n=1024)
    df_voynichese <- density(voynichese[,var], from=lower_limit, to=upper_limit, n=1024)
    qt_meaningful <- quantile(meaningful[,var], probs = c(0.05, 0.5, 0.95))
    qt_gibberish  <- quantile(gibberish[,var], probs = c(0.05, 0.5, 0.95))
    qt_voynichese <- quantile(voynichese[,var], probs = c(0.05, 0.5, 0.95))
    df_overlap    <- tibble(x = df_meaningful$x, y1 = df_meaningful$y, y2 = df_gibberish$y, y3 = df_voynichese$y) %>%
                         mutate(intersect1 = pmin(y1, y2), # intersection between gibberish and meaningful
                                union1 = pmax(y1, y2))
    overlap1 <- sum(df_overlap$intersect1) / sum(df_overlap$union1) # jaccard distance between gibberish and meaningful
    overlap2 <- sum(df_gibberish$y[which(df_gibberish$x >= qt_meaningful[1] & df_gibberish$x <= qt_meaningful[3])]) / sum(df_gibberish$y)
    overlap3 <- sum(df_voynichese$y[which(df_voynichese$x >= qt_meaningful[1] & df_voynichese$x <= qt_meaningful[3])]) / sum(df_voynichese$y)
    overlap4 <- sum(df_voynichese$y[which(df_voynichese$x >= qt_gibberish[1] & df_voynichese$x <= qt_gibberish[3])]) / sum(df_voynichese$y)
    overlap[which(overlap$var == var),"overlap1"] = overlap1 # jaccard distance between gibberish and natural language
    overlap[which(overlap$var == var),"overlap2"] = overlap2 # % of gibberish that looks like natural language
    overlap[which(overlap$var == var),"overlap3"] = overlap3 # % of voynichese that looks like natural language
    overlap[which(overlap$var == var),"overlap4"] = overlap4 # % of voynichese that looks like gibberish
    
    # calculate normalized ranges
    quantiles_gibberish  <- quantile((metrics %>% filter(class == comparison_class))[,var], c(0.05, 0.5, 0.95))
    quantiles_meaningful <- quantile((metrics %>% filter(class == "Natural" | class == "Conlangs"))[,var], c(0.05, 0.5, 0.95))
    quantiles_voynich    <- quantile((metrics %>% filter(class == "Voynichese"))[,var], c(0.05, 0.5, 0.95))
    meaningful_range <- quantiles_meaningful[3] - quantiles_meaningful[1]
    norm_row <- tibble(var = c(var),
                       median = c((quantiles_meaningful[2] / meaningful_range - quantiles_meaningful[1] / meaningful_range)),
                       x1 = c((quantiles_gibberish[1] / meaningful_range - quantiles_meaningful[1] / meaningful_range)),
                       x2 = c((quantiles_gibberish[2] / meaningful_range - quantiles_meaningful[1] / meaningful_range)),
                       x3 = c((quantiles_gibberish[3] / meaningful_range - quantiles_meaningful[1] / meaningful_range)),
                       voyx1 = c((quantiles_voynich[1] / meaningful_range - quantiles_meaningful[1] / meaningful_range)),
                       voyx2 = c((quantiles_voynich[2] / meaningful_range - quantiles_meaningful[1] / meaningful_range)),
                       voyx3 = c((quantiles_voynich[3] / meaningful_range - quantiles_meaningful[1] / meaningful_range)),
                       english = c(median((metrics %>% filter(label == "English"))[,var], na.rm=T) / meaningful_range - quantiles_meaningful[1] / meaningful_range),
                       overlap1 = overlap1,
                       overlap1_class = ifelse(overlap1 >= 0.5, "2", ifelse(overlap1 >= 0.05, "1", "0")),
                       overlap2 = overlap2,
                       overlap2_class = ifelse(overlap2 >= 0.5, "2", ifelse(overlap2 >= 0.05, "1", "0")),
                       overlap3 = overlap3,
                       overlap3_class = ifelse(overlap3 >= 0.5, "2", ifelse(overlap3 >= 0.05, "1", "0")),
                       overlap4 = overlap4,
                       overlap4_class = ifelse(overlap4 >= 0.5, "2", ifelse(overlap4 >= 0.05, "1", "0")))
    norm_ranges <- norm_ranges %>% add_row(norm_row)
}

# normalized range plot
ggplot(norm_ranges) +
    geom_segment(aes(x=voyx1, xend=voyx3, y=var, yend=var), color="pink", size=4) +
    geom_segment(aes(x=x1, xend=x3, y=var, yend=var), color="gray66", size=2) +
    geom_point(aes(x=x2, y=var), size=2, color="gray25") +
    geom_point(aes(x=voyx2, y=var), size=2, color="red") +
    geom_point(aes(x=median, y=var), size=3, color="black", shape=1) +
    geom_point(aes(x=english, y=var), size=2.5, color="black", shape="|") +
    geom_vline(xintercept = 0) +
    geom_vline(xintercept = 1) +
    geom_text(aes(x=-3.5, y=var, color=overlap1_class, label=paste(round(overlap1 * 100), "%", sep="")), size=2.5) +
    geom_text(aes(x=-3.0, y=var, color=overlap2_class, label=paste(round(overlap2 * 100), "%", sep="")), size=2.5) +
    geom_text(aes(x=-2.5, y=var, color=overlap3_class, label=paste(round(overlap3 * 100), "%", sep="")), size=2.5) +
    geom_text(aes(x=-2.0, y=var, color=overlap4_class, label=paste(round(overlap4 * 100), "%", sep="")), size=2.5) +
    scale_color_manual(values=c("0"="red", "1"="chartreuse1", "2"="chartreuse4")) +
    guides(color=F) +
    labs(x = "5-95% quantiles of gibberish (gray) and Voynichese (red) normalized to meaningful text (lines)") +
    theme_bw() +
    coord_cartesian(xlim=c(-3.3, 6)) +
    theme(panel.grid.major = element_blank(),
          panel.grid.minor = element_blank(),
          axis.title.x = element_text(color="black"),
          axis.title.y = element_blank(),
          axis.text.x = element_blank(),
          axis.ticks.x = element_blank(),
          axis.text.y = element_text(color="black"),
          axis.ticks.y = element_line(color="black"))
if (save_files)
    ggsave("ranges.svg", width=8, height=6)
if (unknowledgeable_only)
    ggsave("ranges_unknowledgeable.svg", width=8, height=6)

(max(norm_ranges$x3) - 6) / (6+3.3) # how much further does tripled_words extend?

alpha = 0.05
ttests
ttests_sig <- ttests %>% mutate(G_M = G_M < alpha, G_V = G_V < alpha, V_M = V_M < alpha, G_E = G_E < alpha, S_N = S_N < alpha, class_years = class_years < alpha)
ttests_sig
ttests_dir

# ========================================================================
# Random forest classification
# ========================================================================

metrics_train <- metrics %>% filter(class == "Natural" | class == "Conlangs" | class == "Gibberish")
metrics_train[which(metrics_train$class == "Natural" | metrics_train$class == "Conlangs"),"class"] <- "Meaningful"
metrics_train$factorclass <- as.factor(metrics_train$class)

# classification (more appropriate)
forest_formula <- as.formula(paste("factorclass","~",paste(vars,collapse='+')))
rf = randomForest(forest_formula, ntree = 10000, data = metrics_train, importance=T)
varImpPlot(rf, pch=16, main="Random forest variable importance")
rownames_to_column(data.frame(rf$importance)) %>% arrange(MeanDecreaseAccuracy) %>% select(rowname, MeanDecreaseAccuracy)
if (save_files) {
    dev.copy(svg, "rf_vars.svg", width=10, height=7)
    dev.off()
}
rf_predict <- predict(rf, newdata=metrics_train, type="response")
1 - mean(rf_predict != metrics_train$factorclass) # accuracy!

rf_predict <- predict(rf, newdata=metrics)
predict_class <- data.frame(row.names=metrics$text)
predict_class$class <- rf_predict
noquote("Classification:")
predict_class

rf_predict <- predict(rf, newdata=metrics, type="prob")
predict_probs <- data.frame(row.names=metrics$text)
predict_probs$probability <- sprintf("%1.2f%%", rf_predict[,2]*100)
noquote("Probability of being meaningful:")
predict_probs

metrics_plot <- metrics
metrics_plot$dca1 <- rf_predict[,2]
ridges_plot(metrics_plot, metrics_plot$dca1, "Random forest classification", "Probability of being meaningful")
if (save_files)
    ggsave('class_forest.svg', width=8, height=4)